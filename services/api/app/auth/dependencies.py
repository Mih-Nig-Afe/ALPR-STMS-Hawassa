from __future__ import annotations

from collections.abc import Callable

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.domain import User
from app.services.auth import get_user_by_session_token


def get_current_user_optional(request: Request, db: Session = Depends(get_db)) -> User | None:
    token = request.cookies.get("alpr_session") or request.cookies.get("session")
    cookie_name = request.app.state.settings.session_cookie_name
    token = request.cookies.get(cookie_name) or token
    if not token:
        return None
    return get_user_by_session_token(db, token)


def require_user(current_user: User | None = Depends(get_current_user_optional)) -> User:
    if current_user is None:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            headers={"Location": "/auth/login"},
        )
    return current_user


def require_roles(*allowed_roles: str) -> Callable:
    def dependency(current_user: User = Depends(require_user)) -> User:
        if current_user.role.code not in allowed_roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return current_user

    return dependency
