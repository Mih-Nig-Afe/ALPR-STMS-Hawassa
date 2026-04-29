import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone

from app.core.config import get_settings


PBKDF2_ROUNDS = 390000


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def hash_password(password: str) -> str:
    salt = secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        PBKDF2_ROUNDS,
    )
    return f"pbkdf2_sha256${PBKDF2_ROUNDS}${salt}${digest.hex()}"


def verify_password(password: str, stored_hash: str) -> bool:
    algorithm, rounds, salt, digest = stored_hash.split("$", 3)
    if algorithm != "pbkdf2_sha256":
        return False
    computed = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt.encode("utf-8"),
        int(rounds),
    )
    return hmac.compare_digest(computed.hex(), digest)


def create_session_token() -> str:
    return secrets.token_urlsafe(48)


def hash_session_token(token: str) -> str:
    secret = get_settings().app_secret_key
    return hashlib.sha256(f"{secret}:{token}".encode("utf-8")).hexdigest()


def session_expiry() -> datetime:
    settings = get_settings()
    return utcnow() + timedelta(hours=settings.session_ttl_hours)

