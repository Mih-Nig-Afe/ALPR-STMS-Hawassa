"""End-to-end test driving the full violation lifecycle through the HTTP API."""

from __future__ import annotations

import json
import time
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from alpr_stms_shared.constants import (
    PAYMENT_STATUS_PAID,
    VIOLATION_STATUS_PAID,
    VIOLATION_STATUS_PAYMENT_PENDING,
    VIOLATION_STATUS_UNDER_COMPLAINT,
)
from app.core.config import get_settings
from app.db.session import get_session_factory
from app.main import app
from app.models.domain import (
    AlertRecipient,
    AuditLog,
    Complaint,
    ComplaintDecision,
    OutboxEvent,
    PaymentRequest,
    PaymentTransaction,
    User,
    Violation,
    ViolationAlert,
    ViolationEvidence,
    ViolationRule,
)
from app.services.payment_gateway import (
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    compute_signature,
)


def _login(client: TestClient, username: str, password: str) -> None:
    client.cookies.clear()
    response = client.post(
        "/auth/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )
    assert response.status_code == 303, response.text


def _cleanup_violation(violation_id: str) -> None:
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
def lifecycle_context():
    settings = get_settings()
    factory = get_session_factory()
    with factory() as db:
        rule = db.execute(select(ViolationRule).where(ViolationRule.is_active.is_(True))).scalars().first()
        if rule is None:
            pytest.skip("Seed data missing: no active violation rule")
        rule_id = rule.id
    suffix = uuid4().hex[:8]
    submission_ref = f"E2E-{suffix}"
    plate = f"E2E-{suffix.upper()}"
    created: list[str] = []
    yield {
        "settings": settings,
        "rule_id": rule_id,
        "submission_ref": submission_ref,
        "plate": plate,
        "created": created,
    }
    for vid in created:
        _cleanup_violation(vid)


def _violation_id_from_redirect(location: str) -> str:
    path = location.split("?", 1)[0]
    return path.rsplit("/", 1)[-1]


def test_full_violation_lifecycle_through_http(lifecycle_context) -> None:
    settings = lifecycle_context["settings"]
    rule_id = lifecycle_context["rule_id"]
    submission_ref = lifecycle_context["submission_ref"]
    plate = lifecycle_context["plate"]

    with TestClient(app) as client:
        # 1. Officer logs in and submits a violation
        _login(client, "traffic.officer1", settings.officer_default_password)
        submit = client.post(
            "/violations",
            data={
                "rule_id": rule_id,
                "vehicle_plate": plate,
                "location_text": "E2E Junction",
                "submission_ref": submission_ref,
            },
            follow_redirects=False,
        )
        assert submit.status_code == 303, submit.text
        violation_id = _violation_id_from_redirect(submit.headers["location"])
        lifecycle_context["created"].append(violation_id)

        # 2. Officer views their violations list and the new violation appears
        listing = client.get("/violations")
        assert listing.status_code == 200
        assert submission_ref in listing.text

        # 3. Subcity officer logs in, sees the alert, and acknowledges it
        factory = get_session_factory()
        with factory() as db:
            alert = (
                db.execute(select(ViolationAlert).where(ViolationAlert.violation_id == violation_id)).scalars().one()
            )
            recipients = db.execute(select(AlertRecipient).where(AlertRecipient.alert_id == alert.id)).scalars().all()
            subcity_recipient = next(r for r in recipients if db.get(User, r.user_id).username == "subcity.central")
            recipient_id = subcity_recipient.id
        _login(client, "subcity.central", settings.subcity_default_password)
        ack = client.post(f"/alerts/{recipient_id}/ack", follow_redirects=False)
        assert ack.status_code == 303, ack.text

        # 4. Officer marks the stop outcome as disputed, opening a complaint
        _login(client, "traffic.officer1", settings.officer_default_password)
        dispute = client.post(
            f"/violations/{violation_id}/stop-outcome",
            data={"outcome": "disputed", "notes": "driver disputes"},
            follow_redirects=False,
        )
        assert dispute.status_code == 303, dispute.text
        with factory() as db:
            violation = db.get(Violation, violation_id)
            assert violation.status == VIOLATION_STATUS_UNDER_COMPLAINT
            complaint = db.execute(select(Complaint).where(Complaint.violation_id == violation_id)).scalars().one()
            complaint_id = complaint.id

        # 5. Complaint officer logs in and confirms the complaint
        _login(client, "complaints.officer", settings.complaint_default_password)
        decide = client.post(
            f"/complaints/{complaint_id}/decision",
            data={"decision": "confirm", "notes": "evidence supports citation"},
            follow_redirects=False,
        )
        assert decide.status_code == 303, decide.text
        with factory() as db:
            violation = db.get(Violation, violation_id)
            assert violation.status == VIOLATION_STATUS_PAYMENT_PENDING
            payment_request = (
                db.execute(select(PaymentRequest).where(PaymentRequest.violation_id == violation_id)).scalars().one()
            )
            payment_reference = payment_request.reference_code

        # 6. External payment gateway calls the signed callback to settle
        body = {
            "payment_reference": payment_reference,
            "provider_reference": f"GW-{uuid4().hex[:8]}",
            "outcome": "success",
            "amount": str(payment_request.amount),
        }
        raw = json.dumps(body).encode("utf-8")
        timestamp = int(time.time())
        signature = compute_signature(settings.payment_callback_shared_secret, timestamp, raw)
        callback = client.post(
            "/payments/callback",
            content=raw,
            headers={
                SIGNATURE_HEADER: signature,
                TIMESTAMP_HEADER: str(timestamp),
                "Content-Type": "application/json",
            },
        )
        assert callback.status_code == 200, callback.text
        body_out = callback.json()
        assert body_out["payment_status"] == PAYMENT_STATUS_PAID
        assert body_out["violation_status"] == VIOLATION_STATUS_PAID
        assert body_out["idempotent"] is False

        # 7. Final state in DB matches gateway response
        with factory() as db:
            violation = db.get(Violation, violation_id)
            payment_request = db.get(PaymentRequest, payment_request.id)
            assert violation.status == VIOLATION_STATUS_PAID
            assert payment_request.status == PAYMENT_STATUS_PAID
