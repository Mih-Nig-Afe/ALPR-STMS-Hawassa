from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session, joinedload

from alpr_stms_shared.constants import (
    ROLE_SYSTEM_ADMIN,
    ROLE_TRAFFIC_OFFICER,
    VIOLATION_STATUS_BROADCASTED,
    VIOLATION_STATUS_CONFIRMED,
    VIOLATION_STATUS_PAID,
    VIOLATION_STATUS_PAYMENT_PENDING,
    VIOLATION_STATUS_REPORTED,
    VIOLATION_STATUS_REVOKED,
    VIOLATION_STATUS_UNDER_COMPLAINT,
)
from app.auth.dependencies import require_roles, require_user
from app.core.templating import templates
from app.db.session import get_db
from app.models.domain import User, Violation, ViolationEvidence, ViolationRule
from app.services.workflows import ViolationInput, apply_stop_outcome, create_violation
from app.storage.client import StorageClient

router = APIRouter(prefix="/violations", tags=["violations"])

VIOLATION_STATUS_OPTIONS: tuple[str, ...] = (
    VIOLATION_STATUS_REPORTED,
    VIOLATION_STATUS_BROADCASTED,
    VIOLATION_STATUS_UNDER_COMPLAINT,
    VIOLATION_STATUS_CONFIRMED,
    VIOLATION_STATUS_PAYMENT_PENDING,
    VIOLATION_STATUS_PAID,
    VIOLATION_STATUS_REVOKED,
)


@router.get("")
def violations_page(
    request: Request,
    q: str | None = None,
    status: str | None = None,
    current_user: User = Depends(require_roles(ROLE_TRAFFIC_OFFICER, ROLE_SYSTEM_ADMIN)),
    db: Session = Depends(get_db),
):
    rules = (
        db.execute(select(ViolationRule).where(ViolationRule.is_active.is_(True)).order_by(ViolationRule.name))
        .scalars()
        .all()
    )
    query = (
        select(Violation)
        .options(joinedload(Violation.rule), joinedload(Violation.evidence_items))
        .where(Violation.reporting_officer_id == current_user.id)
        .order_by(Violation.created_at.desc())
    )
    q_clean = (q or "").strip()
    status_clean = (status or "").strip().upper() or None
    if q_clean:
        like = f"%{q_clean.upper()}%"
        query = query.where(
            or_(
                func.upper(Violation.vehicle_plate).like(like),
                func.upper(Violation.reference_code).like(like),
            )
        )
    if status_clean and status_clean in VIOLATION_STATUS_OPTIONS:
        query = query.where(Violation.status == status_clean)
    violations = db.execute(query).unique().scalars().all()
    return templates.TemplateResponse(
        request,
        "violations/index.html",
        {
            "current_user": current_user,
            "rules": rules,
            "violations": violations,
            "filters": {
                "q": q_clean,
                "status": status_clean,
                "status_options": list(VIOLATION_STATUS_OPTIONS),
            },
        },
    )


@router.post("")
async def create_violation_submit(
    request: Request,
    rule_id: str = Form(...),
    vehicle_plate: str = Form(...),
    driver_phone_number: str | None = Form(default=None),
    location_text: str = Form(...),
    latitude: str | None = Form(default=None),
    longitude: str | None = Form(default=None),
    escape_path_geojson: str | None = Form(default=None),
    notes: str | None = Form(default=None),
    submission_ref: str = Form(...),
    evidence: UploadFile | None = File(default=None),
    current_user: User = Depends(require_roles(ROLE_TRAFFIC_OFFICER, ROLE_SYSTEM_ADMIN)),
    db: Session = Depends(get_db),
):
    evidence_bytes = await evidence.read() if evidence and evidence.filename else None
    violation = create_violation(
        db,
        actor=current_user,
        payload=ViolationInput(
            rule_id=rule_id,
            vehicle_plate=vehicle_plate,
            driver_phone_number=driver_phone_number,
            location_text=location_text,
            latitude=latitude,
            longitude=longitude,
            escape_path_geojson=escape_path_geojson,
            notes=notes,
            submission_ref=submission_ref,
        ),
        evidence_filename=evidence.filename if evidence else None,
        evidence_bytes=evidence_bytes,
        evidence_content_type=evidence.content_type if evidence else None,
    )
    params = urlencode({"notice": f"Violation {violation.reference_code} saved", "notice_level": "success"})
    return RedirectResponse(f"/violations/{violation.id}?{params}", status_code=303)


@router.get("/{violation_id}")
def violation_detail(
    violation_id: str,
    request: Request,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    violation = (
        db.execute(
            select(Violation)
            .options(
                joinedload(Violation.rule),
                joinedload(Violation.reporting_officer),
                joinedload(Violation.subcity),
                joinedload(Violation.evidence_items),
                joinedload(Violation.complaints),
                joinedload(Violation.payment_requests),
            )
            .where(Violation.id == violation_id)
        )
        .unique()
        .scalars()
        .first()
    )
    if violation is None:
        raise HTTPException(status_code=404, detail="Violation not found")
    return templates.TemplateResponse(
        request,
        "violations/detail.html",
        {"current_user": current_user, "violation": violation},
    )


@router.post("/{violation_id}/stop-outcome")
def stop_outcome_submit(
    violation_id: str,
    outcome: str = Form(...),
    notes: str | None = Form(default=None),
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    apply_stop_outcome(
        db,
        actor=current_user,
        violation_id=violation_id,
        outcome=outcome,
        notes=notes,
    )
    params = urlencode({"notice": "Stop outcome recorded", "notice_level": "success"})
    return RedirectResponse(f"/violations/{violation_id}?{params}", status_code=303)


@router.get("/evidence/{evidence_id}")
def evidence_download(
    evidence_id: str,
    current_user: User = Depends(require_user),
    db: Session = Depends(get_db),
):
    evidence = db.get(ViolationEvidence, evidence_id)
    if evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    content, content_type = StorageClient().download(
        bucket_name=evidence.bucket_name,
        object_path=evidence.storage_key,
    )
    return StreamingResponse(iter([content]), media_type=content_type)
