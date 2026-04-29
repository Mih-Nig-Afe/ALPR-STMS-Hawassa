from __future__ import annotations

import json
import time
from decimal import Decimal
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from alpr_stms_shared.constants import (
    PAYMENT_STATUS_FAILED,
    PAYMENT_STATUS_PAID,
    PAYMENT_STATUS_REQUESTED,
    ROLE_TRAFFIC_OFFICER,
    VIOLATION_STATUS_PAID,
    VIOLATION_STATUS_PAYMENT_PENDING,
)
from app.core.config import get_settings
from app.core.security import utcnow
from app.db.session import get_session_factory
from app.main import app
from app.models.domain import (
    AuditLog,
    OutboxEvent,
    PaymentRequest,
    PaymentTransaction,
    Role,
    User,
    Violation,
    ViolationRule,
)
from app.services.payment_gateway import (
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    compute_signature,
)

client = TestClient(app)


@pytest.fixture()
def seeded_payment_request():
    settings = get_settings()
    factory = get_session_factory()
    suffix = uuid4().hex[:8]
    payment_id: str | None = None
    violation_id: str | None = None

    with factory() as db:
        rule = db.execute(
            select(ViolationRule).where(ViolationRule.is_active.is_(True))
        ).scalars().first()
        officer = db.execute(
            select(User)
            .join(Role, User.role_id == Role.id)
            .where(Role.code == ROLE_TRAFFIC_OFFICER)
        ).scalars().first()
        if rule is None or officer is None:
            pytest.skip("Seed data missing required rule or officer")

        violation_id = str(uuid4())
        payment_id = str(uuid4())
        reference_code = f"TEST-{suffix}"
        db.add(
            Violation(
                id=violation_id,
                reference_code=reference_code,
                rule_id=rule.id,
                reporting_officer_id=officer.id,
                subcity_id=officer.default_subcity_id,
                vehicle_plate=f"AA-{suffix.upper()}",
                status=VIOLATION_STATUS_PAYMENT_PENDING,
                draft_penalty_amount=Decimal("100.00"),
                location_text="Test corner",
                reported_at=utcnow(),
                created_at=utcnow(),
                updated_at=utcnow(),
            )
        )
        db.add(
            PaymentRequest(
                id=payment_id,
                violation_id=violation_id,
                reference_code=f"PAY-{reference_code}",
                amount=Decimal("100.00"),
                status=PAYMENT_STATUS_REQUESTED,
                requested_at=utcnow(),
                created_by_user_id=officer.id,
            )
        )
        db.commit()

    yield {
        "payment_id": payment_id,
        "violation_id": violation_id,
        "reference_code": f"PAY-TEST-{suffix}",
        "secret": settings.payment_callback_shared_secret,
    }

    with factory() as db:
        db.execute(
            PaymentTransaction.__table__.delete().where(
                PaymentTransaction.payment_request_id == payment_id
            )
        )
        db.execute(AuditLog.__table__.delete().where(AuditLog.entity_id == payment_id))
        for event in db.execute(select(OutboxEvent)).scalars():
            payload = event.payload or {}
            if payload.get("payment_request_id") == payment_id:
                db.delete(event)
        db.execute(
            PaymentRequest.__table__.delete().where(PaymentRequest.id == payment_id)
        )
        db.execute(Violation.__table__.delete().where(Violation.id == violation_id))
        db.commit()


def _signed_request(secret: str, body: dict) -> tuple[bytes, dict[str, str]]:
    raw = json.dumps(body).encode("utf-8")
    timestamp = int(time.time())
    signature = compute_signature(secret, timestamp, raw)
    return raw, {
        SIGNATURE_HEADER: signature,
        TIMESTAMP_HEADER: str(timestamp),
        "Content-Type": "application/json",
    }


def test_callback_rejects_missing_signature(seeded_payment_request) -> None:
    body = {
        "payment_reference": seeded_payment_request["reference_code"],
        "provider_reference": "GW-1",
        "outcome": "success",
    }
    response = client.post(
        "/payments/callback",
        content=json.dumps(body),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401


def test_callback_accepts_valid_signature_and_marks_paid(seeded_payment_request) -> None:
    body = {
        "payment_reference": seeded_payment_request["reference_code"],
        "provider_reference": f"GW-{uuid4().hex[:6]}",
        "outcome": "success",
        "amount": "100.00",
    }
    raw, headers = _signed_request(seeded_payment_request["secret"], body)
    response = client.post("/payments/callback", content=raw, headers=headers)
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["status"] == "accepted"
    assert data["payment_status"] == PAYMENT_STATUS_PAID
    assert data["violation_status"] == VIOLATION_STATUS_PAID
    assert data["idempotent"] is False

    replay = client.post("/payments/callback", content=raw, headers=headers)
    assert replay.status_code == 200
    assert replay.json()["idempotent"] is True


def test_callback_failure_outcome_marks_payment_failed(seeded_payment_request) -> None:
    body = {
        "payment_reference": seeded_payment_request["reference_code"],
        "provider_reference": f"GW-{uuid4().hex[:6]}",
        "outcome": "failure",
    }
    raw, headers = _signed_request(seeded_payment_request["secret"], body)
    response = client.post("/payments/callback", content=raw, headers=headers)
    assert response.status_code == 200
    assert response.json()["payment_status"] == PAYMENT_STATUS_FAILED
