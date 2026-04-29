from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from alpr_stms_shared.constants import (
    ALERT_STATUS_ACKNOWLEDGED,
    ALERT_STATUS_PENDING,
    ROLE_SYSTEM_ADMIN,
)
from app.auth.dependencies import require_user
from app.core.templating import templates
from app.db.session import get_db
from app.models.domain import AlertRecipient, User, ViolationAlert
from app.services.workflows import acknowledge_alert

router = APIRouter(prefix="/alerts", tags=["alerts"])

ALERT_STATUS_OPTIONS: tuple[str, ...] = (ALERT_STATUS_PENDING, ALERT_STATUS_ACKNOWLEDGED)


@router.get("")
def alerts_page(
    request: Request,
    status: str | None = None,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    query = (
        select(AlertRecipient)
        .options(
            joinedload(AlertRecipient.alert).joinedload(ViolationAlert.violation),
            joinedload(AlertRecipient.user),
        )
        .order_by(AlertRecipient.created_at.desc())
    )
    if current_user.role.code != ROLE_SYSTEM_ADMIN:
        query = query.where(AlertRecipient.user_id == current_user.id)
    status_clean = (status or "").strip().upper() or None
    if status_clean in ALERT_STATUS_OPTIONS:
        query = query.where(AlertRecipient.status == status_clean)
    recipients = db.execute(query).scalars().all()
    return templates.TemplateResponse(
        request,
        "alerts/index.html",
        {
            "current_user": current_user,
            "recipients": recipients,
            "filters": {
                "status": status_clean,
                "status_options": list(ALERT_STATUS_OPTIONS),
            },
        },
    )


@router.post("/{recipient_id}/ack")
def acknowledge_alert_submit(
    recipient_id: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    acknowledge_alert(db, actor=current_user, recipient_id=recipient_id)
    params = urlencode({"notice": "Alert acknowledged", "notice_level": "success"})
    return RedirectResponse(f"/alerts?{params}", status_code=303)
