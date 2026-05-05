from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from alpr_stms_shared.constants import ROLE_SYSTEM_ADMIN
from app.auth.dependencies import require_roles
from app.core.templating import templates
from app.db.session import get_db
from app.models.domain import (
    AuditLog,
    PaymentRequest,
    Role,
    Subcity,
    User,
    Violation,
    ViolationRule,
)
from app.services.workflows import create_user_account, reset_user_account_password, toggle_user_account_active

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("")
def admin_page(
    request: Request,
    current_user: User = Depends(require_roles(ROLE_SYSTEM_ADMIN)),
    db: Session = Depends(get_db),
):
    total_users = db.execute(select(func.count(User.id))).scalar_one()
    total_violations = db.execute(select(func.count(Violation.id))).scalar_one()
    total_rules = db.execute(select(func.count(ViolationRule.id))).scalar_one()
    total_subcities = db.execute(select(func.count(Subcity.id))).scalar_one()
    total_payments = db.execute(select(func.count(PaymentRequest.id))).scalar_one()
    recent_audits = db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(20)).scalars().all()
    users = (
        db.execute(
            select(User)
            .options(joinedload(User.role), joinedload(User.default_subcity))
            .order_by(User.created_at.desc())
            .limit(50)
        )
        .scalars()
        .all()
    )
    roles = db.execute(select(Role).order_by(Role.name)).scalars().all()
    subcities = (
        db.execute(select(Subcity).order_by(Subcity.name)).scalars().all()
    )
    user_counts_by_subcity = dict(
        db.execute(
            select(User.default_subcity_id, func.count(User.id)).group_by(User.default_subcity_id)
        ).all()
    )
    return templates.TemplateResponse(
        request,
        "admin/index.html",
        {
            "current_user": current_user,
            "stats": {
                "total_users": total_users,
                "total_violations": total_violations,
                "total_rules": total_rules,
                "total_subcities": total_subcities,
                "total_payments": total_payments,
            },
            "recent_audits": recent_audits,
            "users": users,
            "roles": roles,
            "subcities": subcities,
            "user_counts_by_subcity": user_counts_by_subcity,
        },
    )


@router.post("/users")
def admin_create_user(
    username: str = Form(...),
    full_name: str = Form(...),
    role_id: str = Form(...),
    subcity_id: str | None = Form(default=None),
    password: str = Form(...),
    phone_number: str | None = Form(default=None),
    current_user: User = Depends(require_roles(ROLE_SYSTEM_ADMIN)),
    db: Session = Depends(get_db),
):
    try:
        create_user_account(
            db,
            actor=current_user,
            username=username,
            full_name=full_name,
            password=password,
            role_id=role_id,
            subcity_id=subcity_id or None,
            phone_number=phone_number,
        )
    except ValueError as exc:
        params = urlencode({"notice": str(exc), "notice_level": "danger"})
        return RedirectResponse(f"/admin?{params}", status_code=303)
    params = urlencode({"notice": "User created", "notice_level": "success"})
    return RedirectResponse(f"/admin?{params}", status_code=303)


@router.post("/users/{user_id}/toggle-active")
def admin_toggle_user_active(
    user_id: str,
    current_user: User = Depends(require_roles(ROLE_SYSTEM_ADMIN)),
    db: Session = Depends(get_db),
):
    toggle_user_account_active(db, actor=current_user, user_id=user_id)
    params = urlencode({"notice": "User status updated", "notice_level": "success"})
    return RedirectResponse(f"/admin?{params}", status_code=303)


@router.post("/users/{user_id}/reset-password")
def admin_reset_user_password(
    user_id: str,
    password: str = Form(...),
    current_user: User = Depends(require_roles(ROLE_SYSTEM_ADMIN)),
    db: Session = Depends(get_db),
):
    reset_user_account_password(db, actor=current_user, user_id=user_id, password=password)
    params = urlencode({"notice": "Password reset", "notice_level": "success"})
    return RedirectResponse(f"/admin?{params}", status_code=303)
