from __future__ import annotations

from uuid import uuid4

from fastapi import APIRouter, Depends, Form
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from alpr_stms_shared.constants import ROLE_SYSTEM_ADMIN, ROLE_TRAFFIC_OFFICER
from app.auth.dependencies import require_roles
from app.core.security import utcnow
from app.db.session import get_db
from app.models.domain import OfficerLocation, User

router = APIRouter(prefix="/api", tags=["api"])


@router.post("/officers/location")
def update_officer_location(
    latitude: str = Form(...),
    longitude: str = Form(...),
    current_user: User = Depends(require_roles(ROLE_TRAFFIC_OFFICER, ROLE_SYSTEM_ADMIN)),
    db: Session = Depends(get_db),
):
    db.add(
        OfficerLocation(
            id=str(uuid4()),
            user_id=current_user.id,
            latitude=latitude,
            longitude=longitude,
            captured_at=utcnow(),
            created_at=utcnow(),
        )
    )
    db.commit()
    return JSONResponse({"ok": True})
