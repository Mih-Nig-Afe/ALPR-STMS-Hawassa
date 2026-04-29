from __future__ import annotations

from uuid import uuid4

from sqlalchemy.orm import Session

from alpr_stms_shared.constants import OUTBOX_STATUS_PENDING
from app.core.security import utcnow
from app.models.domain import AuditLog, OutboxEvent, User


def append_audit(
    db: Session,
    *,
    actor: User | None,
    action: str,
    entity_type: str,
    entity_id: str,
    details: dict | None = None,
) -> None:
    db.add(
        AuditLog(
            id=str(uuid4()),
            actor_user_id=actor.id if actor else None,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            created_at=utcnow(),
        )
    )


def enqueue_event(db: Session, *, topic: str, payload: dict) -> None:
    db.add(
        OutboxEvent(
            id=str(uuid4()),
            topic=topic,
            payload=payload,
            status=OUTBOX_STATUS_PENDING,
            attempts=0,
            available_at=utcnow(),
            created_at=utcnow(),
        )
    )
