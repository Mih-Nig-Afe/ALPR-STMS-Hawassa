from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from alpr_stms_shared.constants import (
    ALERT_STATUS_ACKNOWLEDGED,
    ALERT_STATUS_PENDING,
    COMPLAINT_STATUS_CONFIRMED,
    COMPLAINT_STATUS_OPEN,
    COMPLAINT_STATUS_REVOKED,
    PAYMENT_STATUS_FAILED,
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_REQUESTED,
    ROLE_SUBCITY_OFFICER,
    ROLE_SYSTEM_ADMIN,
    VIOLATION_STATUS_BROADCASTED,
    VIOLATION_STATUS_PAID,
    VIOLATION_STATUS_PAYMENT_PENDING,
    VIOLATION_STATUS_REPORTED,
    VIOLATION_STATUS_REVOKED,
    VIOLATION_STATUS_UNDER_COMPLAINT,
)
from app.core.security import utcnow
from app.models.domain import (
    AlertRecipient,
    Complaint,
    ComplaintDecision,
    PaymentRequest,
    PaymentTransaction,
    User,
    Violation,
    ViolationAlert,
    ViolationEvidence,
    ViolationRule,
)
from app.services.audit import append_audit, enqueue_event
from app.storage.client import StorageClient


@dataclass
class ViolationInput:
    rule_id: str
    vehicle_plate: str
    driver_phone_number: str | None
    location_text: str
    latitude: str | None
    longitude: str | None
    escape_path_geojson: str | None
    notes: str | None
    submission_ref: str


def _parse_geojson(raw: str | None) -> dict | None:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"raw": raw}


def _recipient_users(db: Session, actor: User) -> list[User]:
    return (
        db.execute(
            select(User)
            .options(joinedload(User.role))
            .where(User.is_active.is_(True))
            .where(User.role.has(code=ROLE_SYSTEM_ADMIN) | User.role.has(code=ROLE_SUBCITY_OFFICER))
        )
        .scalars()
        .all()
    )


def _ensure_payment_request(db: Session, actor: User, violation: Violation) -> PaymentRequest:
    existing = (
        db.execute(select(PaymentRequest).where(PaymentRequest.violation_id == violation.id))
        .scalars()
        .first()
    )
    if existing:
        return existing
    payment_request = PaymentRequest(
        id=str(uuid4()),
        violation_id=violation.id,
        reference_code=f"PAY-{violation.reference_code}",
        amount=Decimal(violation.draft_penalty_amount),
        status=PAYMENT_STATUS_REQUESTED,
        requested_at=utcnow(),
        created_by_user_id=actor.id,
    )
    db.add(payment_request)
    enqueue_event(
        db,
        topic="payment.requested",
        payload={"payment_request_id": payment_request.id, "violation_id": violation.id},
    )
    append_audit(
        db,
        actor=actor,
        action="payment.requested",
        entity_type="payment_request",
        entity_id=payment_request.id,
        details={"violation_id": violation.id, "amount": str(payment_request.amount)},
    )
    return payment_request


def create_violation(
    db: Session,
    *,
    actor: User,
    payload: ViolationInput,
    evidence_filename: str | None,
    evidence_bytes: bytes | None,
    evidence_content_type: str | None,
) -> Violation:
    existing = (
        db.execute(select(Violation).where(Violation.reference_code == payload.submission_ref))
        .scalars()
        .first()
    )
    if existing:
        return existing

    rule = db.get(ViolationRule, payload.rule_id)
    if rule is None:
        raise ValueError("Violation rule not found")
    if actor.default_subcity is None:
        raise ValueError("Officer is missing a default subcity")

    violation = Violation(
        id=str(uuid4()),
        reference_code=payload.submission_ref,
        rule_id=rule.id,
        reporting_officer_id=actor.id,
        subcity_id=actor.default_subcity.id,
        vehicle_plate=payload.vehicle_plate.upper().strip(),
        driver_phone_number=payload.driver_phone_number,
        status=VIOLATION_STATUS_REPORTED,
        draft_penalty_amount=Decimal(rule.penalty_amount),
        location_text=payload.location_text.strip(),
        latitude=payload.latitude,
        longitude=payload.longitude,
        escape_path_geojson=_parse_geojson(payload.escape_path_geojson),
        notes=payload.notes,
        reported_at=utcnow(),
        created_at=utcnow(),
        updated_at=utcnow(),
    )
    db.add(violation)
    db.flush()
    append_audit(
        db,
        actor=actor,
        action="violation.reported",
        entity_type="violation",
        entity_id=violation.id,
        details={"status": VIOLATION_STATUS_REPORTED},
    )

    if evidence_filename and evidence_bytes:
        stored = StorageClient().upload(
            object_path=f"{violation.id}/{evidence_filename}",
            content=evidence_bytes,
            content_type=evidence_content_type or "application/octet-stream",
        )
        db.add(
            ViolationEvidence(
                id=str(uuid4()),
                violation_id=violation.id,
                bucket_name=stored.bucket_name,
                storage_key=stored.storage_key,
                original_filename=evidence_filename,
                mime_type=stored.mime_type,
                byte_size=stored.byte_size,
                sha256_hex=stored.sha256_hex,
                created_at=utcnow(),
            )
        )
        append_audit(
            db,
            actor=actor,
            action="violation.evidence_uploaded",
            entity_type="violation",
            entity_id=violation.id,
            details={"filename": evidence_filename},
        )

    alert = ViolationAlert(
        id=str(uuid4()),
        violation_id=violation.id,
        message=f"Violation {violation.reference_code} reported in {actor.default_subcity.name}",
        created_by_user_id=actor.id,
        created_at=utcnow(),
    )
    db.add(alert)
    db.flush()
    for recipient in _recipient_users(db, actor):
        db.add(
            AlertRecipient(
                id=str(uuid4()),
                alert_id=alert.id,
                user_id=recipient.id,
                status=ALERT_STATUS_PENDING,
                created_at=utcnow(),
            )
        )

    violation.status = VIOLATION_STATUS_BROADCASTED
    violation.updated_at = utcnow()
    append_audit(
        db,
        actor=actor,
        action="violation.broadcasted",
        entity_type="violation",
        entity_id=violation.id,
        details={"status": VIOLATION_STATUS_BROADCASTED},
    )
    enqueue_event(
        db,
        topic="alerts.broadcast",
        payload={"violation_id": violation.id, "alert_id": alert.id},
    )
    db.commit()
    db.refresh(violation)
    return violation


def acknowledge_alert(db: Session, *, actor: User, recipient_id: str) -> None:
    recipient = db.get(AlertRecipient, recipient_id)
    if recipient is None:
        raise ValueError("Alert recipient not found")
    if recipient.user_id != actor.id and actor.role.code != ROLE_SYSTEM_ADMIN:
        raise PermissionError("Cannot acknowledge another user's alert")
    recipient.status = ALERT_STATUS_ACKNOWLEDGED
    recipient.acknowledged_at = utcnow()
    append_audit(
        db,
        actor=actor,
        action="alert.acknowledged",
        entity_type="alert_recipient",
        entity_id=recipient.id,
        details={"alert_id": recipient.alert_id},
    )
    db.commit()


def apply_stop_outcome(db: Session, *, actor: User, violation_id: str, outcome: str, notes: str | None) -> None:
    violation = db.get(Violation, violation_id)
    if violation is None:
        raise ValueError("Violation not found")

    if outcome == "admitted":
        violation.status = VIOLATION_STATUS_PAYMENT_PENDING
        _ensure_payment_request(db, actor, violation)
        append_audit(
            db,
            actor=actor,
            action="violation.admitted",
            entity_type="violation",
            entity_id=violation.id,
            details={"notes": notes},
        )
    elif outcome == "disputed":
        violation.status = VIOLATION_STATUS_UNDER_COMPLAINT
        complaint = Complaint(
            id=str(uuid4()),
            violation_id=violation.id,
            opened_by_user_id=actor.id,
            status=COMPLAINT_STATUS_OPEN,
            reason=notes or "Disputed during stop outcome review",
            created_at=utcnow(),
        )
        db.add(complaint)
        append_audit(
            db,
            actor=actor,
            action="complaint.opened",
            entity_type="complaint",
            entity_id=complaint.id,
            details={"violation_id": violation.id},
        )
    else:
        raise ValueError("Unsupported stop outcome")

    violation.updated_at = utcnow()
    db.commit()


def decide_complaint(db: Session, *, actor: User, complaint_id: str, decision: str, notes: str | None) -> None:
    complaint = (
        db.execute(
            select(Complaint).options(joinedload(Complaint.violation)).where(Complaint.id == complaint_id)
        )
        .scalars()
        .first()
    )
    if complaint is None:
        raise ValueError("Complaint not found")

    db.add(
        ComplaintDecision(
            id=str(uuid4()),
            complaint_id=complaint.id,
            decided_by_user_id=actor.id,
            decision=decision,
            notes=notes,
            created_at=utcnow(),
        )
    )

    if decision == "confirm":
        complaint.status = COMPLAINT_STATUS_CONFIRMED
        complaint.violation.status = VIOLATION_STATUS_PAYMENT_PENDING
        _ensure_payment_request(db, actor, complaint.violation)
    elif decision == "revoke":
        complaint.status = COMPLAINT_STATUS_REVOKED
        complaint.violation.status = VIOLATION_STATUS_REVOKED
    else:
        raise ValueError("Unsupported complaint decision")

    complaint.violation.updated_at = utcnow()
    append_audit(
        db,
        actor=actor,
        action="complaint.decided",
        entity_type="complaint",
        entity_id=complaint.id,
        details={"decision": decision, "notes": notes},
    )
    db.commit()


@dataclass
class PaymentCallbackResult:
    payment_request_id: str
    payment_status: str
    violation_status: str
    transaction_id: str
    provider_reference: str
    idempotent: bool


def _record_payment_outcome(
    db: Session,
    *,
    actor: User | None,
    payment_request: PaymentRequest,
    provider_reference: str,
    outcome: str,
    payload: dict,
    audit_action: str,
) -> PaymentCallbackResult:
    existing = (
        db.execute(
            select(PaymentTransaction).where(
                PaymentTransaction.payment_request_id == payment_request.id,
                PaymentTransaction.provider_reference == provider_reference,
            )
        )
        .scalars()
        .first()
    )
    if existing is not None:
        return PaymentCallbackResult(
            payment_request_id=payment_request.id,
            payment_status=payment_request.status,
            violation_status=payment_request.violation.status,
            transaction_id=existing.id,
            provider_reference=existing.provider_reference,
            idempotent=True,
        )

    transaction = PaymentTransaction(
        id=str(uuid4()),
        payment_request_id=payment_request.id,
        provider_reference=provider_reference,
        outcome=outcome,
        payload=payload,
        created_at=utcnow(),
    )
    db.add(transaction)

    if outcome == "success":
        payment_request.status = PAYMENT_STATUS_PAID
        payment_request.violation.status = VIOLATION_STATUS_PAID
    else:
        payment_request.status = PAYMENT_STATUS_FAILED
        payment_request.violation.status = VIOLATION_STATUS_PAYMENT_PENDING

    payment_request.violation.updated_at = utcnow()
    append_audit(
        db,
        actor=actor,
        action=audit_action,
        entity_type="payment_request",
        entity_id=payment_request.id,
        details={"outcome": outcome, "provider_reference": provider_reference},
    )
    enqueue_event(
        db,
        topic="payment.settled",
        payload={
            "payment_request_id": payment_request.id,
            "outcome": outcome,
            "provider_reference": provider_reference,
        },
    )
    return PaymentCallbackResult(
        payment_request_id=payment_request.id,
        payment_status=payment_request.status,
        violation_status=payment_request.violation.status,
        transaction_id=transaction.id,
        provider_reference=provider_reference,
        idempotent=False,
    )


def simulate_payment_callback(
    db: Session,
    *,
    actor: User,
    payment_request_id: str,
    outcome: str,
    notes: str | None,
) -> PaymentCallbackResult:
    payment_request = (
        db.execute(
            select(PaymentRequest)
            .options(joinedload(PaymentRequest.violation))
            .where(PaymentRequest.id == payment_request_id)
        )
        .scalars()
        .first()
    )
    if payment_request is None:
        raise ValueError("Payment request not found")

    provider_reference = f"SIM-{payment_request.reference_code}-{uuid4().hex[:8]}"
    result = _record_payment_outcome(
        db,
        actor=actor,
        payment_request=payment_request,
        provider_reference=provider_reference,
        outcome=outcome,
        payload={"notes": notes, "simulated": True},
        audit_action="payment.callback.simulated",
    )
    db.commit()
    return result


def apply_gateway_callback(
    db: Session,
    *,
    payment_reference: str,
    provider_reference: str,
    outcome: str,
    raw_payload: dict,
) -> PaymentCallbackResult:
    if outcome not in {"success", "failure"}:
        raise ValueError("Unsupported callback outcome")
    payment_request = (
        db.execute(
            select(PaymentRequest)
            .options(joinedload(PaymentRequest.violation))
            .where(PaymentRequest.reference_code == payment_reference)
        )
        .scalars()
        .first()
    )
    if payment_request is None:
        raise LookupError("Payment request not found for reference")
    result = _record_payment_outcome(
        db,
        actor=None,
        payment_request=payment_request,
        provider_reference=provider_reference,
        outcome=outcome,
        payload=raw_payload,
        audit_action="payment.callback.gateway",
    )
    db.commit()
    return result
