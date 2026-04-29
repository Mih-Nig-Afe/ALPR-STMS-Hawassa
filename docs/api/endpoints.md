# Phase 1 API reference

This document enumerates every HTTP route exposed by the Phase 1 FastAPI service.
Most routes are HTML (server-rendered Jinja2 templates) and consume `multipart/form-data`
or `application/x-www-form-urlencoded`; the gateway callback is the only first-class
JSON endpoint. Authentication is by signed cookie (`Set-Cookie` issued by `POST /auth/login`)
unless otherwise noted.

## Roles

| Code | Description |
| --- | --- |
| `traffic_officer` | Submits violations, acknowledges alerts. |
| `subcity_officer` | Receives broadcast alerts within their subcity. |
| `complaint_officer` | Reviews disputes and settles payments. |
| `system_admin` | Full access; can read all alerts and the audit summary. |

## Health

| Method | Path | Auth | Response |
| --- | --- | --- | --- |
| `GET` | `/health/live` | none | `200 {"status":"ok"}` |
| `GET` | `/health/ready` | none | `200 {"status":"ok","storage":true}` or `503 {"status":"degraded","storage":false}` |

## Auth

| Method | Path | Auth | Form fields | Behaviour |
| --- | --- | --- | --- | --- |
| `GET` | `/auth/login` | none | – | Renders the login page; redirects to `/` if already signed in. |
| `POST` | `/auth/login` | none | `username`, `password` | Issues session cookie on success, redirects to `/`. On failure redirects back with `?notice=Invalid credentials`. |
| `POST` | `/auth/logout` | session | – | Deletes session and clears cookie. |

## Home and PWA

| Method | Path | Auth | Behaviour |
| --- | --- | --- | --- |
| `GET` | `/` | optional session | Role-based redirect: traffic→`/violations`, complaint→`/complaints`, admin→`/admin`, others→`/alerts`. Anonymous→`/auth/login`. |
| `GET` | `/manifest.webmanifest` | none | Returns the PWA manifest. |

## Violations

| Method | Path | Roles | Form fields | Behaviour |
| --- | --- | --- | --- | --- |
| `GET` | `/violations` | `traffic_officer`, `system_admin` | – | Renders the officer's submitted violations and active rules. |
| `POST` | `/violations` | `traffic_officer`, `system_admin` | `rule_id`, `vehicle_plate`, `driver_phone_number?`, `location_text`, `latitude?`, `longitude?`, `escape_path_geojson?`, `notes?`, `submission_ref`, `evidence?` (file) | Creates a violation, optionally uploads evidence to Supabase Storage, broadcasts alerts, writes audit log. Redirects to `/violations/{id}` on success. |
| `GET` | `/violations/{violation_id}` | session | – | Renders the detail page for a single violation. `404` if missing. |
| `POST` | `/violations/{violation_id}/stop-outcome` | session | `outcome`, `notes?` | Records the on-stop outcome (e.g. driver flees, complies). |
| `GET` | `/violations/evidence/{evidence_id}` | session | – | Streams the stored evidence file from Supabase Storage. `404` if missing. |

`submission_ref` is an idempotency token the form generates client-side; resubmitting with the same value returns the existing violation.

## Alerts

| Method | Path | Auth | Behaviour |
| --- | --- | --- | --- |
| `GET` | `/alerts` | session | Renders alert recipients for the current user (or all of them for `system_admin`). |
| `POST` | `/alerts/{recipient_id}/ack` | session | Marks a recipient row as `ACKNOWLEDGED`, writes audit, redirects with success notice. |

## Complaints

| Method | Path | Roles | Form fields | Behaviour |
| --- | --- | --- | --- | --- |
| `GET` | `/complaints` | `complaint_officer`, `system_admin` | – | Renders the complaint queue with linked violations and prior decisions. |
| `POST` | `/complaints/{complaint_id}/decision` | `complaint_officer`, `system_admin` | `decision` (`CONFIRMED`/`REVOKED`), `notes?` | Records the complaint decision, updates the parent violation status, writes audit, possibly issues a payment request. |

## Payments

| Method | Path | Auth | Form / body | Behaviour |
| --- | --- | --- | --- | --- |
| `GET` | `/payments` | `complaint_officer`, `system_admin` | – | Renders the payment-request queue with related transactions. |
| `POST` | `/payments/{payment_request_id}/simulate` | `complaint_officer`, `system_admin` | `outcome`, `notes?` | Manually settles a payment request through the internal simulator (bypasses HMAC; UI-only). |
| `POST` | `/payments/callback` | HMAC | JSON body, `X-Timestamp`, `X-Signature` | Public webhook for real gateways. See [`docs/integrations/payment-callback.md`](../integrations/payment-callback.md) for the full contract. |

The callback endpoint is the only route that returns JSON natively. Status codes:

| Status | Meaning |
| --- | --- |
| `200` | Settlement applied (or idempotent replay). Body includes `payment_status`, `violation_status`, `transaction_id`. |
| `400` | Malformed body or unsupported `outcome`. |
| `401` | Missing/invalid signature, or timestamp drift > 5 minutes. |
| `404` | `payment_reference` does not match any payment request. |

## Admin

| Method | Path | Roles | Behaviour |
| --- | --- | --- | --- |
| `GET` | `/admin` | `system_admin` | Renders the dashboard with totals (users, violations, rules) and the 20 most-recent audit entries. |

## Static assets

| Method | Path | Behaviour |
| --- | --- | --- |
| `GET` | `/static/...` | Serves bundled CSS/JS/icons from `services/api/app/static`. |

## Workflow state machines

Every state-mutating route writes to `audit_logs` and, where applicable, enqueues an `outbox_events` row for the worker to deliver downstream. Authoritative transitions:

- **violation.status**: `REPORTED → BROADCASTED → UNDER_COMPLAINT → (CONFIRMED|REVOKED) → PAYMENT_PENDING → (PAID|FAILED→PAYMENT_PENDING)`.
- **alert_recipient.status**: `PENDING → ACKNOWLEDGED`.
- **complaint.status**: `OPEN → (CONFIRMED|REVOKED)`.
- **payment_request.status**: `REQUESTED → (PAID|FAILED)`; failures keep the violation in `PAYMENT_PENDING` so the gateway can retry.

All transitions are idempotent at the domain layer (`apply_gateway_callback` keys on `(payment_request_id, provider_reference)`; `create_violation` keys on `submission_ref`).
