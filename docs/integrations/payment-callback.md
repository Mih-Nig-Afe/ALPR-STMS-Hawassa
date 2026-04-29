# Payment gateway callback contract

This document describes the HTTP contract a payment gateway must satisfy to settle
violation payments via the Phase 1 platform. The endpoint is signed and idempotent
so that real providers can safely retry on transient failures.

## Endpoint

```
POST /payments/callback
Content-Type: application/json
```

The endpoint is publicly reachable (no session cookie required) but every request
must carry a valid HMAC signature derived from the shared secret stored in
`PAYMENT_CALLBACK_SHARED_SECRET`.

## Headers

| Header | Required | Description |
| --- | --- | --- |
| `Content-Type` | Yes | Must be `application/json`. |
| `X-Timestamp` | Yes | Unix epoch seconds (UTC) when the request was generated. |
| `X-Signature` | Yes | Lowercase hex HMAC-SHA256 over `f"{X-Timestamp}.{raw_body}"` keyed with the shared secret. |

The server rejects requests whose timestamp drifts more than 5 minutes from the
server clock to mitigate replay attacks.

## Request body

```json
{
  "payment_reference": "PAY-VIO-2026-000123",
  "provider_reference": "GW-7F1A8C",
  "outcome": "success",
  "amount": "1200.00",
  "paid_at": "2026-04-29T11:24:00Z",
  "metadata": { "channel": "ussd", "msisdn": "+251911000000" }
}
```

| Field | Required | Description |
| --- | --- | --- |
| `payment_reference` | Yes | The `reference_code` of the `payment_request` issued by the platform. |
| `provider_reference` | Yes | Stable identifier from the gateway. Used for idempotency. |
| `outcome` | Yes | `success` or `failure`. |
| `amount`, `paid_at`, `metadata` | No | Stored verbatim on the resulting `payment_transactions.payload`. |

## Responses

| Status | Body | Meaning |
| --- | --- | --- |
| `200` | `{"status": "accepted", "idempotent": false, ...}` | Callback applied for the first time. |
| `200` | `{"status": "accepted", "idempotent": true, ...}` | Replay of an already-recorded `provider_reference`. No state change. |
| `400` | `{"detail": "..."}` | Malformed JSON, missing fields, or unsupported `outcome`. |
| `401` | `{"detail": "..."}` | Missing or invalid signature, expired timestamp. |
| `404` | `{"detail": "Payment request not found for reference"}` | Unknown `payment_reference`. |

The success body includes the resulting `payment_status` (`PAID` / `FAILED`),
`violation_status` (`PAID` / `PAYMENT_PENDING`), `transaction_id`, and
`payment_request_id` for downstream reconciliation.

## Signing example (Python)

```python
import hashlib
import hmac
import json
import time

import httpx

SECRET = "the-shared-secret-from-env"
body = {
    "payment_reference": "PAY-VIO-2026-000123",
    "provider_reference": "GW-7F1A8C",
    "outcome": "success",
}
raw = json.dumps(body).encode("utf-8")
timestamp = int(time.time())
signature = hmac.new(
    SECRET.encode("utf-8"),
    f"{timestamp}.".encode("utf-8") + raw,
    hashlib.sha256,
).hexdigest()
httpx.post(
    "https://stms.example.com/payments/callback",
    content=raw,
    headers={
        "Content-Type": "application/json",
        "X-Timestamp": str(timestamp),
        "X-Signature": signature,
    },
    timeout=10,
)
```

## Side effects

A successful (or idempotent replay) callback:

1. Inserts a `payment_transactions` row keyed by `(payment_request_id, provider_reference)`.
2. Updates `payment_requests.status` to `PAID` or `FAILED`.
3. Updates the linked `violations.status` to `PAID` (success) or `PAYMENT_PENDING` (failure).
4. Writes an `audit_logs` entry with action `payment.callback.gateway`.
5. Enqueues an `outbox_events` entry on topic `payment.settled` for downstream notification.

## Operational notes

- Rotate `PAYMENT_CALLBACK_SHARED_SECRET` per environment. Production secrets live
  outside the repository and must be injected via the deployment environment.
- The internal "Simulate" button on the payments page calls
  `simulate_payment_callback` directly through the authenticated UI. It is
  intended for manual testing only and bypasses the HMAC contract.
- Outbox delivery happens asynchronously via the worker; callers must not depend
  on it for response correctness.
