from fastapi import APIRouter, Depends, Request
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from alpr_stms_shared.constants import ROLE_SYSTEM_ADMIN
from app.auth.dependencies import require_roles
from app.core.templating import templates
from app.db.session import get_db
from app.models.domain import AuditLog, User, Violation, ViolationRule


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
    recent_audits = db.execute(select(AuditLog).order_by(AuditLog.created_at.desc()).limit(20)).scalars().all()
    return templates.TemplateResponse(
        request,
        "admin/index.html",
        {
            "current_user": current_user,
            "stats": {
                "total_users": total_users,
                "total_violations": total_violations,
                "total_rules": total_rules,
            },
            "recent_audits": recent_audits,
        },
    )
