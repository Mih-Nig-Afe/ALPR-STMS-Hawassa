from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.security import (
    create_session_token,
    hash_session_token,
    session_expiry,
    utcnow,
    verify_password,
)
from app.models.domain import SessionModel, User


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = (
        db.execute(
            select(User)
            .options(joinedload(User.role), joinedload(User.default_subcity))
            .where(User.username == username)
        )
        .scalars()
        .first()
    )
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


def create_session(
    db: Session,
    *,
    user: User,
    ip_address: str | None,
    user_agent: str | None,
) -> str:
    raw_token = create_session_token()
    db.add(
        SessionModel(
            id=str(uuid4()),
            user_id=user.id,
            token_hash=hash_session_token(raw_token),
            expires_at=session_expiry(),
            ip_address=ip_address,
            user_agent=user_agent,
            last_seen_at=utcnow(),
            created_at=utcnow(),
        )
    )
    db.commit()
    return raw_token


def get_user_by_session_token(db: Session, token: str) -> User | None:
    session_record = (
        db.execute(
            select(SessionModel)
            .options(joinedload(SessionModel.user).joinedload(User.role), joinedload(SessionModel.user).joinedload(User.default_subcity))
            .where(SessionModel.token_hash == hash_session_token(token))
        )
        .scalars()
        .first()
    )
    if session_record is None or session_record.expires_at <= utcnow():
        return None
    session_record.last_seen_at = utcnow()
    db.commit()
    return session_record.user


def delete_session(db: Session, token: str) -> None:
    session_record = (
        db.execute(select(SessionModel).where(SessionModel.token_hash == hash_session_token(token)))
        .scalars()
        .first()
    )
    if session_record:
        db.delete(session_record)
        db.commit()
