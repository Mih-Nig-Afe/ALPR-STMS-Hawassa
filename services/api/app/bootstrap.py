from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.orm import Session

from alpr_stms_shared.constants import (
    ROLE_COMPLAINT_OFFICER,
    ROLE_SUBCITY_OFFICER,
    ROLE_SYSTEM_ADMIN,
    ROLE_TRAFFIC_OFFICER,
)
from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import get_session_factory
from app.models.domain import OfficerAssignment, Role, Subcity, User, ViolationRule
from app.storage.client import StorageClient

ROOT = Path(__file__).resolve().parents[3]
SEED_DIR = ROOT / "data" / "seed" / "json"


def _load_json(name: str) -> list[dict]:
    with (SEED_DIR / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _upsert_roles(db: Session) -> dict[str, Role]:
    role_map = {
        ROLE_TRAFFIC_OFFICER: "Traffic Officer",
        ROLE_SUBCITY_OFFICER: "Subcity Officer",
        ROLE_COMPLAINT_OFFICER: "Complaint Officer",
        ROLE_SYSTEM_ADMIN: "System Administrator",
    }
    roles: dict[str, Role] = {}
    for code, name in role_map.items():
        role = db.execute(select(Role).where(Role.code == code)).scalars().first()
        if role is None:
            role = Role(id=str(uuid4()), code=code, name=name)
            db.add(role)
        else:
            role.name = name
        roles[code] = role
    db.flush()
    return roles


def _upsert_subcities(db: Session) -> dict[str, Subcity]:
    subcities: dict[str, Subcity] = {}
    for item in _load_json("subcities.json"):
        subcity = db.execute(select(Subcity).where(Subcity.code == item["code"])).scalars().first()
        if subcity is None:
            subcity = Subcity(id=str(uuid4()), code=item["code"], name=item["name"], is_active=True)
            db.add(subcity)
        else:
            subcity.name = item["name"]
            subcity.is_active = True
        subcities[item["code"]] = subcity
    db.flush()
    return subcities


def _upsert_rules(db: Session) -> None:
    for item in _load_json("violation_rules.json"):
        rule = db.execute(select(ViolationRule).where(ViolationRule.code == item["code"])).scalars().first()
        if rule is None:
            rule = ViolationRule(
                id=str(uuid4()),
                code=item["code"],
                name=item["name"],
                description=item["description"],
                penalty_amount=item["penalty_amount"],
                is_active=True,
            )
            db.add(rule)
        else:
            rule.name = item["name"]
            rule.description = item["description"]
            rule.penalty_amount = item["penalty_amount"]
            rule.is_active = True
    db.flush()


def _upsert_user(
    db: Session,
    *,
    username: str,
    full_name: str,
    role: Role,
    subcity: Subcity | None,
    password: str,
    phone_number: str,
) -> User:
    user = db.execute(select(User).where(User.username == username)).scalars().first()
    if user is None:
        user = User(
            id=str(uuid4()),
            username=username,
            full_name=full_name,
            phone_number=phone_number,
            password_hash=hash_password(password),
            role_id=role.id,
            default_subcity_id=subcity.id if subcity else None,
            is_active=True,
        )
        db.add(user)
    else:
        user.full_name = full_name
        user.role_id = role.id
        user.default_subcity_id = subcity.id if subcity else None
        user.password_hash = hash_password(password)
        user.is_active = True
    db.flush()
    return user


def _ensure_assignment(db: Session, *, user: User, subcity: Subcity, title: str) -> None:
    assignment = (
        db.execute(
            select(OfficerAssignment)
            .where(OfficerAssignment.user_id == user.id)
            .where(OfficerAssignment.subcity_id == subcity.id)
        )
        .scalars()
        .first()
    )
    if assignment is None:
        db.add(
            OfficerAssignment(
                id=str(uuid4()),
                user_id=user.id,
                subcity_id=subcity.id,
                title=title,
                is_primary=True,
                is_active=True,
            )
        )


def run_bootstrap() -> None:
    settings = get_settings()
    session_factory = get_session_factory()
    with session_factory() as db:
        roles = _upsert_roles(db)
        subcities = _upsert_subcities(db)
        _upsert_rules(db)

        central = subcities["central-hawassa"]
        east = subcities["east-hawassa"]

        users_to_seed = [
            ("TP1", "Traffic Police Officer 1", roles[ROLE_TRAFFIC_OFFICER], central, "tp1alprstms", "+251900000001"),
            ("TP2", "Traffic Police Officer 2", roles[ROLE_TRAFFIC_OFFICER], central, "tp2alprstms", "+251900000002"),
            ("TP3", "Traffic Police Officer 3", roles[ROLE_TRAFFIC_OFFICER], east, "tp3alprstms", "+251900000003"),
            ("SC1", "Subcity Officer 1", roles[ROLE_SUBCITY_OFFICER], central, "sc1alprstms", "+251900000004"),
            ("SC2", "Subcity Officer 2", roles[ROLE_SUBCITY_OFFICER], east, "sc2alprstms", "+251900000005"),
            ("CO1", "Complaint Officer 1", roles[ROLE_COMPLAINT_OFFICER], central, "co1alprstms", "+251900000006"),
            ("CO2", "Complaint Officer 2", roles[ROLE_COMPLAINT_OFFICER], east, "co2alprstms", "+251900000007"),
            ("ADMIN1", "System Administrator", roles[ROLE_SYSTEM_ADMIN], central, "admin1alprstms", "+251900000008"),
        ]

        seeded_users: list[tuple[User, Subcity, str]] = []
        for username, full_name, role, subcity, password, phone in users_to_seed:
            user = _upsert_user(
                db,
                username=username,
                full_name=full_name,
                role=role,
                subcity=subcity,
                password=password,
                phone_number=phone,
            )
            seeded_users.append((user, subcity, role.name))

        for user, subcity, title in seeded_users:
            _ensure_assignment(db, user=user, subcity=subcity, title=title)
        db.commit()

    client = StorageClient()
    try:
        client.ensure_bucket()
    except Exception:
        if settings.app_env != "development":
            raise


if __name__ == "__main__":
    run_bootstrap()
