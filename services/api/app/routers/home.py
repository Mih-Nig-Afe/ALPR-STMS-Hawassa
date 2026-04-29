from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from sqlalchemy import text
from sqlalchemy.orm import Session

from alpr_stms_shared.constants import (
    ROLE_COMPLAINT_OFFICER,
    ROLE_SYSTEM_ADMIN,
    ROLE_TRAFFIC_OFFICER,
)
from app.auth.dependencies import get_current_user_optional
from app.db.session import get_db
from app.models.domain import User
from app.storage.client import StorageClient

router = APIRouter()


@router.get("/", include_in_schema=False)
def index(current_user: User | None = Depends(get_current_user_optional)):
    if current_user is None:
        return RedirectResponse("/auth/login", status_code=303)
    if current_user.role.code == ROLE_TRAFFIC_OFFICER:
        return RedirectResponse("/violations", status_code=303)
    if current_user.role.code == ROLE_COMPLAINT_OFFICER:
        return RedirectResponse("/complaints", status_code=303)
    if current_user.role.code == ROLE_SYSTEM_ADMIN:
        return RedirectResponse("/admin", status_code=303)
    return RedirectResponse("/alerts", status_code=303)


@router.get("/health/live", tags=["health"])
def live() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@router.get("/health/ready", tags=["health"])
def ready(db: Session = Depends(get_db)) -> JSONResponse:
    db.execute(text("SELECT 1"))
    try:
        storage_ok = StorageClient().status()
    except Exception:
        storage_ok = False
    payload = {"status": "ok" if storage_ok else "degraded", "storage": storage_ok}
    return JSONResponse(payload, status_code=200 if storage_ok else 503)


@router.get("/manifest.webmanifest", include_in_schema=False)
def manifest() -> FileResponse:
    path = Path(__file__).resolve().parent.parent / "static" / "manifest.webmanifest"
    return FileResponse(path, media_type="application/manifest+json")


@router.get("/service-worker.js", include_in_schema=False)
def service_worker() -> FileResponse:
    path = Path(__file__).resolve().parent.parent / "static" / "js" / "service-worker.js"
    return FileResponse(path, media_type="application/javascript")
