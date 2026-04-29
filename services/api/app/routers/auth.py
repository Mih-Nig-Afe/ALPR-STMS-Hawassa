from __future__ import annotations

from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user_optional
from app.core.config import get_settings
from app.core.templating import templates
from app.db.session import get_db
from app.models.domain import User
from app.services.auth import authenticate_user, create_session, delete_session

router = APIRouter(prefix="/auth", tags=["auth"])


@router.get("/login")
def login_page(request: Request, current_user: User | None = Depends(get_current_user_optional)):
    if current_user is not None:
        return RedirectResponse("/", status_code=303)
    return templates.TemplateResponse(request, "auth/login.html", {})


@router.post("/login")
def login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = authenticate_user(db, username=username.strip(), password=password)
    if user is None:
        params = urlencode({"notice": "Invalid credentials", "notice_level": "danger"})
        return RedirectResponse(f"/auth/login?{params}", status_code=303)

    raw_token = create_session(
        db,
        user=user,
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent"),
    )
    settings = get_settings()
    response = RedirectResponse("/", status_code=303)
    response.set_cookie(
        settings.session_cookie_name,
        raw_token,
        httponly=True,
        secure=settings.secure_cookies,
        samesite="lax",
        max_age=settings.session_ttl_hours * 3600,
    )
    return response


@router.post("/logout")
def logout(request: Request, db: Session = Depends(get_db)):
    settings = get_settings()
    token = request.cookies.get(settings.session_cookie_name)
    if token:
        delete_session(db, token)
    response = RedirectResponse("/auth/login", status_code=303)
    response.delete_cookie(settings.session_cookie_name)
    return response
