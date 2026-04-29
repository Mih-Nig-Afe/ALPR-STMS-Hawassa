from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass

SIGNATURE_HEADER = "X-Signature"
TIMESTAMP_HEADER = "X-Timestamp"

MAX_SIGNATURE_AGE_SECONDS = 300


class CallbackSignatureError(Exception):
    """Raised when a callback signature cannot be validated."""


@dataclass(frozen=True)
class SignedPayload:
    timestamp: int
    raw_body: bytes


def compute_signature(secret: str, timestamp: int, raw_body: bytes) -> str:
    message = f"{timestamp}.".encode() + raw_body
    digest = hmac.new(secret.encode("utf-8"), message, hashlib.sha256).hexdigest()
    return digest


def verify_signature(
    *,
    secret: str,
    timestamp_header: str | None,
    signature_header: str | None,
    raw_body: bytes,
    now_epoch: int,
    max_age_seconds: int = MAX_SIGNATURE_AGE_SECONDS,
) -> SignedPayload:
    if not secret:
        raise CallbackSignatureError("Callback secret is not configured")
    if not signature_header:
        raise CallbackSignatureError(f"Missing {SIGNATURE_HEADER} header")
    if not timestamp_header:
        raise CallbackSignatureError(f"Missing {TIMESTAMP_HEADER} header")
    try:
        timestamp = int(timestamp_header)
    except ValueError as exc:
        raise CallbackSignatureError("Invalid timestamp header") from exc
    if abs(now_epoch - timestamp) > max_age_seconds:
        raise CallbackSignatureError("Callback timestamp outside of acceptance window")
    expected = compute_signature(secret, timestamp, raw_body)
    if not hmac.compare_digest(expected, signature_header.strip().lower()):
        raise CallbackSignatureError("Signature mismatch")
    return SignedPayload(timestamp=timestamp, raw_body=raw_body)
