from __future__ import annotations

import json
import time
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from alpr_stms_shared.constants import ROLE_COMPLAINT_OFFICER, ROLE_SYSTEM_ADMIN
from app.auth.dependencies import require_roles
from app.core.config import get_settings
from app.core.templating import templates
from app.db.session import get_db
from app.models.domain import PaymentRequest, User, Violation
from app.services.payment_gateway import (
    SIGNATURE_HEADER,
    TIMESTAMP_HEADER,
    CallbackSignatureError,
    verify_signature,
)
from app.services.workflows import apply_gateway_callback, simulate_payment_callback

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
        .unique()
        .scalars()
        .all()
    )
    return templates.TemplateResponse(
        request,
        "payments/index.html",
        {"current_user": current_user, "payment_requests": payment_requests},
    )


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


@router.post("/callback", include_in_schema=True)
async def gateway_callback(request: Request, db: Session = Depends(get_db)) -> JSONResponse:
    settings = get_settings()
    raw_body = await request.body()
    try:
        verify_signature(
            secret=settings.payment_callback_shared_secret,
            timestamp_header=request.headers.get(TIMESTAMP_HEADER),
            signature_header=request.headers.get(SIGNATURE_HEADER),
            raw_body=raw_body,
            now_epoch=int(time.time()),
        )
    except CallbackSignatureError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    try:
        payload = json.loads(raw_body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid JSON body",
        ) from exc
    if not isinstance(payload, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Body must be a JSON object",
        )

    payment_reference = payload.get("payment_reference")
    provider_reference = payload.get("provider_reference")
    outcome = payload.get("outcome")
    if not payment_reference or not provider_reference or not outcome:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="payment_reference, provider_reference, and outcome are required",
        )

    try:
        result = apply_gateway_callback(
            db,
            payment_reference=str(payment_reference),
            provider_reference=str(provider_reference),
            outcome=str(outcome),
            raw_payload=payload,
        )
    except LookupError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return JSONResponse(
        {
            "status": "accepted",
            "idempotent": result.idempotent,
            "payment_request_id": result.payment_request_id,
            "payment_status": result.payment_status,
            "violation_status": result.violation_status,
            "transaction_id": result.transaction_id,
            "provider_reference": result.provider_reference,
        }
    )
