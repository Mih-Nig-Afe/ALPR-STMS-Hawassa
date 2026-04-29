from __future__ import annotations

import pytest

from app.services.payment_gateway import (
    CallbackSignatureError,
    compute_signature,
    verify_signature,
)

SECRET = "test-callback-secret"
BODY = b'{"payment_reference":"PAY-123","provider_reference":"GW-1","outcome":"success"}'


def test_compute_signature_is_deterministic() -> None:
    first = compute_signature(SECRET, 1700000000, BODY)
    second = compute_signature(SECRET, 1700000000, BODY)
    assert first == second


def test_compute_signature_changes_with_body() -> None:
    first = compute_signature(SECRET, 1700000000, BODY)
    second = compute_signature(SECRET, 1700000000, BODY + b" ")
    assert first != second


def test_verify_signature_accepts_matching_payload() -> None:
    timestamp = 1700000000
    signature = compute_signature(SECRET, timestamp, BODY)
    payload = verify_signature(
        secret=SECRET,
        timestamp_header=str(timestamp),
        signature_header=signature,
        raw_body=BODY,
        now_epoch=timestamp + 5,
    )
    assert payload.timestamp == timestamp
    assert payload.raw_body == BODY


def test_verify_signature_rejects_when_secret_missing() -> None:
    with pytest.raises(CallbackSignatureError):
        verify_signature(
            secret="",
            timestamp_header="1",
            signature_header="x",
            raw_body=BODY,
            now_epoch=1,
        )


def test_verify_signature_rejects_missing_headers() -> None:
    with pytest.raises(CallbackSignatureError):
        verify_signature(
            secret=SECRET,
            timestamp_header=None,
            signature_header="x",
            raw_body=BODY,
            now_epoch=1,
        )
    with pytest.raises(CallbackSignatureError):
        verify_signature(
            secret=SECRET,
            timestamp_header="1",
            signature_header=None,
            raw_body=BODY,
            now_epoch=1,
        )


def test_verify_signature_rejects_invalid_timestamp() -> None:
    with pytest.raises(CallbackSignatureError):
        verify_signature(
            secret=SECRET,
            timestamp_header="not-an-int",
            signature_header=compute_signature(SECRET, 1, BODY),
            raw_body=BODY,
            now_epoch=1,
        )


def test_verify_signature_rejects_stale_timestamp() -> None:
    timestamp = 1700000000
    signature = compute_signature(SECRET, timestamp, BODY)
    with pytest.raises(CallbackSignatureError):
        verify_signature(
            secret=SECRET,
            timestamp_header=str(timestamp),
            signature_header=signature,
            raw_body=BODY,
            now_epoch=timestamp + 10_000,
        )


def test_verify_signature_rejects_tampered_body() -> None:
    timestamp = 1700000000
    signature = compute_signature(SECRET, timestamp, BODY)
    with pytest.raises(CallbackSignatureError):
        verify_signature(
            secret=SECRET,
            timestamp_header=str(timestamp),
            signature_header=signature,
            raw_body=BODY + b"x",
            now_epoch=timestamp + 5,
        )


def test_verify_signature_rejects_tampered_signature() -> None:
    timestamp = 1700000000
    signature = compute_signature(SECRET, timestamp, BODY)
    bad_signature = signature[:-1] + ("0" if signature[-1] != "0" else "1")
    with pytest.raises(CallbackSignatureError):
        verify_signature(
            secret=SECRET,
            timestamp_header=str(timestamp),
            signature_header=bad_signature,
            raw_body=BODY,
            now_epoch=timestamp + 5,
        )
