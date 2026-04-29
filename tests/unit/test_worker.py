from __future__ import annotations

from datetime import timedelta
from uuid import uuid4

import pytest
from sqlalchemy import select

from alpr_stms_shared.constants import (
    OUTBOX_STATUS_DELIVERED,
    OUTBOX_STATUS_PENDING,
)
from app.core.security import utcnow
from app.db.session import get_session_factory
from app.models.domain import OutboxEvent
from worker_app.main import process_batch, update_heartbeat


@pytest.fixture()
def pending_outbox_event():
    factory = get_session_factory()
    event_id = str(uuid4())
    with factory() as db:
        db.add(
            OutboxEvent(
                id=event_id,
                topic="test.worker",
                payload={"marker": event_id},
                status=OUTBOX_STATUS_PENDING,
                attempts=0,
                available_at=utcnow() - timedelta(seconds=1),
                created_at=utcnow(),
            )
        )
        db.commit()
    yield event_id
    with factory() as db:
        db.execute(OutboxEvent.__table__.delete().where(OutboxEvent.id == event_id))
        db.commit()


def test_process_batch_marks_pending_event_delivered(pending_outbox_event) -> None:
    processed = process_batch()
    assert processed >= 1
    factory = get_session_factory()
    with factory() as db:
        event = db.execute(select(OutboxEvent).where(OutboxEvent.id == pending_outbox_event)).scalars().one()
        assert event.status == OUTBOX_STATUS_DELIVERED
        assert event.attempts == 1
        assert event.processed_at is not None
        assert event.last_error is None


def test_process_batch_skips_future_available_events() -> None:
    factory = get_session_factory()
    event_id = str(uuid4())
    with factory() as db:
        db.add(
            OutboxEvent(
                id=event_id,
                topic="test.worker.future",
                payload={"marker": event_id},
                status=OUTBOX_STATUS_PENDING,
                attempts=0,
                available_at=utcnow() + timedelta(hours=1),
                created_at=utcnow(),
            )
        )
        db.commit()
    try:
        process_batch()
        with factory() as db:
            event = db.execute(select(OutboxEvent).where(OutboxEvent.id == event_id)).scalars().one()
            assert event.status == OUTBOX_STATUS_PENDING
            assert event.attempts == 0
    finally:
        with factory() as db:
            db.execute(OutboxEvent.__table__.delete().where(OutboxEvent.id == event_id))
            db.commit()


def test_update_heartbeat_writes_iso_timestamp(tmp_path, monkeypatch) -> None:
    target = tmp_path / "heartbeat"
    monkeypatch.setattr("worker_app.main.HEARTBEAT_FILE", target)
    update_heartbeat()
    assert target.exists()
    contents = target.read_text("utf-8")
    assert "T" in contents
