import logging
import time
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import sessionmaker

from alpr_stms_shared.constants import (
    OUTBOX_STATUS_DELIVERED,
    OUTBOX_STATUS_FAILED,
    OUTBOX_STATUS_PENDING,
)
from app.core.config import get_settings
from app.core.security import utcnow
from app.db.session import build_engine
from app.models.domain import OutboxEvent

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
LOGGER = logging.getLogger("alpr-stms-worker")
HEARTBEAT_FILE = Path("/tmp/worker-heartbeat")


def process_batch() -> int:
    settings = get_settings()
    engine = build_engine(settings.worker_database_url)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
    processed = 0
    with SessionLocal() as db:
        events = (
            db.execute(
                select(OutboxEvent)
                .where(OutboxEvent.status == OUTBOX_STATUS_PENDING)
                .where(OutboxEvent.available_at <= utcnow())
                .order_by(OutboxEvent.created_at.asc())
                .limit(settings.worker_batch_size)
            )
            .scalars()
            .all()
        )
        for event in events:
            try:
                event.attempts += 1
                event.status = OUTBOX_STATUS_DELIVERED
                event.processed_at = utcnow()
                event.last_error = None
                processed += 1
            except Exception as exc:
                event.attempts += 1
                event.status = OUTBOX_STATUS_FAILED
                event.last_error = str(exc)
        db.commit()
    return processed


def update_heartbeat() -> None:
    HEARTBEAT_FILE.write_text(utcnow().isoformat(), encoding="utf-8")


def main() -> None:
    settings = get_settings()
    LOGGER.info("Starting worker loop with poll interval %s seconds", settings.worker_poll_seconds)
    while True:
        processed = process_batch()
        update_heartbeat()
        if processed:
            LOGGER.info("Processed %s outbox event(s)", processed)
        time.sleep(settings.worker_poll_seconds)


if __name__ == "__main__":
    main()
