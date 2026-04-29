from __future__ import annotations

from uuid import uuid4

import pytest
from sqlalchemy import select

from alpr_stms_shared.constants import (
    ALERT_STATUS_ACKNOWLEDGED,
    COMPLAINT_STATUS_CONFIRMED,
    COMPLAINT_STATUS_REVOKED,
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_REQUESTED,
    ROLE_COMPLAINT_OFFICER,
    ROLE_TRAFFIC_OFFICER,
    VIOLATION_STATUS_BROADCASTED,
    VIOLATION_STATUS_PAID,
    VIOLATION_STATUS_PAYMENT_PENDING,
    VIOLATION_STATUS_REVOKED,
    VIOLATION_STATUS_UNDER_COMPLAINT,
)
from app.db.session import get_session_factory
from app.models.domain import (
    AlertRecipient,
    AuditLog,
    Complaint,
    ComplaintDecision,
    OutboxEvent,
    PaymentRequest,
    PaymentTransaction,
    Role,
    User,
    Violation,
    ViolationAlert,
    ViolationEvidence,
    ViolationRule,
)
from app.services.workflows import (
    ViolationInput,
    acknowledge_alert,
    apply_stop_outcome,
    create_violation,
    decide_complaint,
    simulate_payment_callback,
)


def _user_with_role(db, code: str):
    return db.execute(select(User).join(Role, User.role_id == Role.id).where(Role.code == code)).scalars().first()


def _cleanup(violation_id: str) -> None:
    factory = get_session_factory()
    with factory() as db:
        payment_ids = [
            row[0]
            for row in db.execute(select(PaymentRequest.id).where(PaymentRequest.violation_id == violation_id)).all()
        ]
        for pid in payment_ids:
            db.execute(PaymentTransaction.__table__.delete().where(PaymentTransaction.payment_request_id == pid))
            db.execute(AuditLog.__table__.delete().where(AuditLog.entity_id == pid))
        db.execute(PaymentRequest.__table__.delete().where(PaymentRequest.violation_id == violation_id))
        complaint_ids = [
            row[0] for row in db.execute(select(Complaint.id).where(Complaint.violation_id == violation_id)).all()
        ]
        for cid in complaint_ids:
            db.execute(ComplaintDecision.__table__.delete().where(ComplaintDecision.complaint_id == cid))
            db.execute(AuditLog.__table__.delete().where(AuditLog.entity_id == cid))
        db.execute(Complaint.__table__.delete().where(Complaint.violation_id == violation_id))
        alert_ids = [
            row[0]
            for row in db.execute(select(ViolationAlert.id).where(ViolationAlert.violation_id == violation_id)).all()
        ]
        for aid in alert_ids:
            db.execute(AlertRecipient.__table__.delete().where(AlertRecipient.alert_id == aid))
        db.execute(ViolationAlert.__table__.delete().where(ViolationAlert.violation_id == violation_id))
        db.execute(ViolationEvidence.__table__.delete().where(ViolationEvidence.violation_id == violation_id))
        db.execute(AuditLog.__table__.delete().where(AuditLog.entity_id == violation_id))
        for event in db.execute(select(OutboxEvent)).scalars():
            payload = event.payload or {}
            if payload.get("violation_id") == violation_id:
                db.delete(event)
        db.execute(Violation.__table__.delete().where(Violation.id == violation_id))
        db.commit()


@pytest.fixture()
def workflow_world():
    factory = get_session_factory()
    suffix = uuid4().hex[:8]
    with factory() as db:
        rule = db.execute(select(ViolationRule).where(ViolationRule.is_active.is_(True))).scalars().first()
        officer = _user_with_role(db, ROLE_TRAFFIC_OFFICER)
        complaint_officer = _user_with_role(db, ROLE_COMPLAINT_OFFICER)
        if rule is None or officer is None or complaint_officer is None:
            pytest.skip("Seed data missing for workflow tests")
        ids = {
            "rule_id": rule.id,
            "officer_id": officer.id,
            "complaint_officer_id": complaint_officer.id,
            "submission_ref": f"WF-{suffix}",
            "plate": f"BB-{suffix.upper()}",
        }
    created: list[str] = []
    yield ids, created
    for vid in created:
        _cleanup(vid)


def _make_violation(officer_id: str, ids: dict, *, plate_suffix: str = "") -> str:
    payload = ViolationInput(
        rule_id=ids["rule_id"],
        vehicle_plate=ids["plate"] + plate_suffix,
        driver_phone_number=None,
        location_text="Workflow Test Junction",
        latitude=None,
        longitude=None,
        escape_path_geojson=None,
        notes=None,
        submission_ref=ids["submission_ref"] + plate_suffix,
    )
    factory = get_session_factory()
    with factory() as db:
        actor = db.get(User, officer_id)
        violation = create_violation(
            db,
            actor=actor,
            payload=payload,
            evidence_filename=None,
            evidence_bytes=None,
            evidence_content_type=None,
        )
        return violation.id


def test_create_violation_broadcasts_and_assigns_recipients(workflow_world) -> None:
    ids, created = workflow_world
    violation_id = _make_violation(ids["officer_id"], ids)
    created.append(violation_id)
    factory = get_session_factory()
    with factory() as db:
        violation = db.get(Violation, violation_id)
        assert violation.status == VIOLATION_STATUS_BROADCASTED
        alert = db.execute(select(ViolationAlert).where(ViolationAlert.violation_id == violation_id)).scalars().one()
        recipients = db.execute(select(AlertRecipient).where(AlertRecipient.alert_id == alert.id)).scalars().all()
        assert recipients, "broadcast must produce at least one recipient"


def test_acknowledge_alert_updates_recipient(workflow_world) -> None:
    ids, created = workflow_world
    violation_id = _make_violation(ids["officer_id"], ids, plate_suffix="A")
    created.append(violation_id)
    factory = get_session_factory()
    with factory() as db:
        alert = db.execute(select(ViolationAlert).where(ViolationAlert.violation_id == violation_id)).scalars().one()
        recipient = db.execute(select(AlertRecipient).where(AlertRecipient.alert_id == alert.id)).scalars().first()
        recipient_user_id = recipient.user_id
        recipient_id = recipient.id
    with factory() as db:
        actor = db.get(User, recipient_user_id)
        acknowledge_alert(db, actor=actor, recipient_id=recipient_id)
    with factory() as db:
        recipient = db.get(AlertRecipient, recipient_id)
        assert recipient.status == ALERT_STATUS_ACKNOWLEDGED
        assert recipient.acknowledged_at is not None


def test_apply_stop_outcome_admitted_creates_payment_request(workflow_world) -> None:
    ids, created = workflow_world
    violation_id = _make_violation(ids["officer_id"], ids, plate_suffix="B")
    created.append(violation_id)
    factory = get_session_factory()
    with factory() as db:
        actor = db.get(User, ids["officer_id"])
        apply_stop_outcome(db, actor=actor, violation_id=violation_id, outcome="admitted", notes="paid on the spot")
    with factory() as db:
        violation = db.get(Violation, violation_id)
        assert violation.status == VIOLATION_STATUS_PAYMENT_PENDING
        payment_request = (
            db.execute(select(PaymentRequest).where(PaymentRequest.violation_id == violation_id)).scalars().one()
        )
        assert payment_request.status == PAYMENT_STATUS_REQUESTED


def test_apply_stop_outcome_disputed_opens_complaint(workflow_world) -> None:
    ids, created = workflow_world
    violation_id = _make_violation(ids["officer_id"], ids, plate_suffix="C")
    created.append(violation_id)
    factory = get_session_factory()
    with factory() as db:
        actor = db.get(User, ids["officer_id"])
        apply_stop_outcome(db, actor=actor, violation_id=violation_id, outcome="disputed", notes="driver disputes")
    with factory() as db:
        violation = db.get(Violation, violation_id)
        assert violation.status == VIOLATION_STATUS_UNDER_COMPLAINT
        complaint = db.execute(select(Complaint).where(Complaint.violation_id == violation_id)).scalars().one()
        assert complaint.status == "OPEN"


def test_decide_complaint_revoke_sets_violation_revoked(workflow_world) -> None:
    ids, created = workflow_world
    violation_id = _make_violation(ids["officer_id"], ids, plate_suffix="D")
    created.append(violation_id)
    factory = get_session_factory()
    with factory() as db:
        actor = db.get(User, ids["officer_id"])
        apply_stop_outcome(db, actor=actor, violation_id=violation_id, outcome="disputed", notes="dispute")
        complaint_id = db.execute(select(Complaint.id).where(Complaint.violation_id == violation_id)).scalar_one()
    with factory() as db:
        actor = db.get(User, ids["complaint_officer_id"])
        decide_complaint(db, actor=actor, complaint_id=complaint_id, decision="revoke", notes="not at fault")
    with factory() as db:
        violation = db.get(Violation, violation_id)
        complaint = db.get(Complaint, complaint_id)
        assert violation.status == VIOLATION_STATUS_REVOKED
        assert complaint.status == COMPLAINT_STATUS_REVOKED


def test_decide_complaint_confirm_creates_payment_request(workflow_world) -> None:
    ids, created = workflow_world
    violation_id = _make_violation(ids["officer_id"], ids, plate_suffix="E")
    created.append(violation_id)
    factory = get_session_factory()
    with factory() as db:
        actor = db.get(User, ids["officer_id"])
        apply_stop_outcome(db, actor=actor, violation_id=violation_id, outcome="disputed", notes="dispute")
        complaint_id = db.execute(select(Complaint.id).where(Complaint.violation_id == violation_id)).scalar_one()
    with factory() as db:
        actor = db.get(User, ids["complaint_officer_id"])
        decide_complaint(db, actor=actor, complaint_id=complaint_id, decision="confirm", notes="confirmed")
    with factory() as db:
        violation = db.get(Violation, violation_id)
        complaint = db.get(Complaint, complaint_id)
        assert violation.status == VIOLATION_STATUS_PAYMENT_PENDING
        assert complaint.status == COMPLAINT_STATUS_CONFIRMED
        payment_request = (
            db.execute(select(PaymentRequest).where(PaymentRequest.violation_id == violation_id)).scalars().one()
        )
        assert payment_request.status == PAYMENT_STATUS_REQUESTED


def test_simulate_payment_callback_marks_paid(workflow_world) -> None:
    ids, created = workflow_world
    violation_id = _make_violation(ids["officer_id"], ids, plate_suffix="F")
    created.append(violation_id)
    factory = get_session_factory()
    with factory() as db:
        actor = db.get(User, ids["officer_id"])
        apply_stop_outcome(db, actor=actor, violation_id=violation_id, outcome="admitted", notes=None)
        payment_request_id = db.execute(
            select(PaymentRequest.id).where(PaymentRequest.violation_id == violation_id)
        ).scalar_one()
    with factory() as db:
        actor = db.get(User, ids["officer_id"])
        result = simulate_payment_callback(
            db, actor=actor, payment_request_id=payment_request_id, outcome="success", notes="ok"
        )
        assert result.payment_status == PAYMENT_STATUS_PAID
        assert result.violation_status == VIOLATION_STATUS_PAID
        assert result.idempotent is False
    with factory() as db:
        violation = db.get(Violation, violation_id)
        assert violation.status == VIOLATION_STATUS_PAID
