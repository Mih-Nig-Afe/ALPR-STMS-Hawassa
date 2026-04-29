from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from alpr_stms_shared.constants import (
    COMPLAINT_STATUS_CONFIRMED,
    COMPLAINT_STATUS_OPEN,
    COMPLAINT_STATUS_REVOKED,
    ROLE_COMPLAINT_OFFICER,
    ROLE_SYSTEM_ADMIN,
)
from app.auth.dependencies import require_roles
from app.core.templating import templates
from app.db.session import get_db
from app.models.domain import Complaint, User, Violation
from app.services.workflows import decide_complaint

router = APIRouter(prefix="/complaints", tags=["complaints"])

COMPLAINT_STATUS_OPTIONS: tuple[str, ...] = (
    COMPLAINT_STATUS_OPEN,
    COMPLAINT_STATUS_CONFIRMED,
    COMPLAINT_STATUS_REVOKED,
)


@router.get("")
def complaints_page(
    request: Request,
    status: str | None = None,
    current_user: User = Depends(require_roles(ROLE_COMPLAINT_OFFICER, ROLE_SYSTEM_ADMIN)),
    db: Session = Depends(get_db),
):
    query = (
        select(Complaint)
        .options(
            joinedload(Complaint.violation).joinedload(Violation.rule),
            joinedload(Complaint.violation).joinedload(Violation.reporting_officer),
            joinedload(Complaint.decisions),
        )
        .order_by(Complaint.created_at.desc())
    )
    status_clean = (status or "").strip().upper() or None
    if status_clean in COMPLAINT_STATUS_OPTIONS:
        query = query.where(Complaint.status == status_clean)
    complaints = db.execute(query).unique().scalars().all()
    return templates.TemplateResponse(
        request,
        "complaints/index.html",
        {
            "current_user": current_user,
            "complaints": complaints,
            "filters": {
                "status": status_clean,
                "status_options": list(COMPLAINT_STATUS_OPTIONS),
            },
        },
    )


@router.post("/{complaint_id}/decision")
def complaint_decision_submit(
    complaint_id: str,
    decision: str = Form(...),
    notes: str | None = Form(default=None),
    current_user: User = Depends(require_roles(ROLE_COMPLAINT_OFFICER, ROLE_SYSTEM_ADMIN)),
    db: Session = Depends(get_db),
):
    decide_complaint(
        db,
        actor=current_user,
        complaint_id=complaint_id,
        decision=decision,
        notes=notes,
    )
    params = urlencode({"notice": "Complaint decision recorded", "notice_level": "success"})
    return RedirectResponse(f"/complaints?{params}", status_code=303)
