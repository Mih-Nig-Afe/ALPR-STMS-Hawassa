from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from alpr_stms_shared.constants import ROLE_SYSTEM_ADMIN
from app.auth.dependencies import require_roles
from app.core.templating import templates
from app.db.session import get_db
from app.models.domain import (
    AuditLog,
    PaymentRequest,
    Subcity,
    User,
    Violation,
    ViolationRule,
)

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
            "subcities": subcities,
            "user_counts_by_subcity": user_counts_by_subcity,
        },
    )
