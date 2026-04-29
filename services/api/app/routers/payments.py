from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from alpr_stms_shared.constants import ROLE_COMPLAINT_OFFICER, ROLE_SYSTEM_ADMIN
from app.auth.dependencies import require_roles
from app.core.templating import templates
from app.db.session import get_db
from app.models.domain import PaymentRequest, User, Violation
from app.services.workflows import simulate_payment_callback


router = APIRouter(prefix="/payments", tags=["payments"])


@router.get("")
def payments_page(
    request: Request,
    current_user: User = Depends(require_roles(ROLE_COMPLAINT_OFFICER, ROLE_SYSTEM_ADMIN)),
    db: Session = Depends(get_db),
):
    payment_requests = (
        db.execute(
            select(PaymentRequest)
            .options(
                joinedload(PaymentRequest.violation).joinedload(Violation.reporting_officer),
                joinedload(PaymentRequest.transactions),
            )
            .order_by(PaymentRequest.requested_at.desc())
        )
        .scalars()
        .all()
    )
    return templates.TemplateResponse(request, "payments/index.html", {"current_user": current_user, "payment_requests": payment_requests})


@router.post("/{payment_request_id}/simulate")
def simulate_payment_submit(
    payment_request_id: str,
    outcome: str = Form(...),
    notes: str | None = Form(default=None),
    current_user: User = Depends(require_roles(ROLE_COMPLAINT_OFFICER, ROLE_SYSTEM_ADMIN)),
    db: Session = Depends(get_db),
):
    simulate_payment_callback(
        db,
        actor=current_user,
        payment_request_id=payment_request_id,
        outcome=outcome,
        notes=notes,
    )
    params = urlencode({"notice": "Payment callback recorded", "notice_level": "success"})
    return RedirectResponse(f"/payments?{params}", status_code=303)
