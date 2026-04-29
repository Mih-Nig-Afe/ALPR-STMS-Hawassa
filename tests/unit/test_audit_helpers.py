from __future__ import annotations

from types import SimpleNamespace

from alpr_stms_shared.constants import OUTBOX_STATUS_PENDING
from app.models.domain import AuditLog, OutboxEvent
from app.services.audit import append_audit, enqueue_event


class _FakeSession:
    def __init__(self) -> None:
        self.added: list = []

    def add(self, instance) -> None:
        self.added.append(instance)


def test_append_audit_writes_audit_log_with_actor() -> None:
    db = _FakeSession()
    actor = SimpleNamespace(id="user-123")
    append_audit(
        db,
        actor=actor,
        action="violation.reported",
        entity_type="violation",
        entity_id="vio-1",
        details={"status": "REPORTED"},
    )
    assert len(db.added) == 1
    record = db.added[0]
    assert isinstance(record, AuditLog)
    assert record.actor_user_id == "user-123"
    assert record.action == "violation.reported"
    assert record.entity_type == "violation"
    assert record.entity_id == "vio-1"
    assert record.details == {"status": "REPORTED"}
    assert record.id


def test_append_audit_handles_no_actor() -> None:
    db = _FakeSession()
    append_audit(
        db,
        actor=None,
        action="payment.callback.gateway",
        entity_type="payment_request",
        entity_id="pay-1",
        details=None,
    )
    record = db.added[0]
    assert record.actor_user_id is None
    assert record.details is None


def test_enqueue_event_creates_pending_outbox_entry() -> None:
    db = _FakeSession()
    enqueue_event(db, topic="payment.settled", payload={"payment_request_id": "p-1"})
    record = db.added[0]
    assert isinstance(record, OutboxEvent)
    assert record.topic == "payment.settled"
    assert record.payload == {"payment_request_id": "p-1"}
    assert record.status == OUTBOX_STATUS_PENDING
    assert record.attempts == 0
    assert record.available_at is not None
