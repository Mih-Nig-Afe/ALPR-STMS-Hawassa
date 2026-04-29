# Changelog

All notable changes to this repository will be documented in this file.

## [Unreleased]

### Added

- `infra/deploy/scripts/first-boot.sh` and `make first-boot` one-shot bootstrap that runs env init, `docker compose up --build`, api healthcheck wait, `alembic upgrade head`, seed bootstrap, and the runtime smoke script
- `scripts/smoke.sh` now also asserts that the proxy renders the login page (title and `<form>` present), catching template-render regressions in addition to the JSON health endpoints

### Changed

- `docs/planning/phase-1-master-tracker.md` Section 16 collapsed to a single solo-author signoff row recording approval of the backend release `v0.1.0-phase1`
- README status block updated to mark Phase 1 backend `v0.1.0-phase1` as released and to advertise the `make first-boot` workflow
- Admin, violations, alerts, complaints, and payments screens now share reusable template macros (`page_title`, `status_badge`, `empty_row`) for consistent table styling and status rendering
- List routes for violations, alerts, complaints, and payments now support status filters and expose the active selection in the UI
- HTML exception handling now renders a consistent dedicated error page for browser clients while API/health routes continue returning JSON responses

## [v0.1.0-phase1] - 2026-04-29

First tagged release of Phase 1 — the manual-enforcement-first **backend
milestone** of the ALPR-Based Smart Traffic Management System for Hawassa City.
Webs and Apps sub-phases of Phase 1 are tracked separately and will be released
under their own tags.

Highlights:

- Production-ready FastAPI backend with cookie-session RBAC, audit logging,
  Supabase storage for evidence, payment-request lifecycle, and HMAC-verified
  payment-gateway callbacks
- Self-hosted Supabase subset (Postgres 15, PostgREST, Storage API, imgproxy)
  orchestrated via `compose.yaml` with healthchecks, separate DB roles, and
  rotated secrets
- Background worker with database outbox pattern for alerts and payment events
- Full Phase 1 schema, migrations (alembic), seed reference data, and seeded
  test users for every role
- Test suite: 37 passing tests across unit, integration, and end-to-end HTTP
  layers; CI runs ruff lint + format + pytest on every push and PR
- Runtime smoke (`make smoke`) covering liveness, readiness, storage, evidence
  upload+download round-trip, and login-page render
- Backup and restore smoke (`make backup-smoke`) verifying 27 public/storage
  tables round-trip through `pg_dump` / `pg_restore`
- Documentation: API reference, payment-callback contract, Docker operations
  and production deployment runbook, ADRs, and a Phase 1 master tracker with
  all nine readiness gates marked Complete

### Added

- Formal repository structure
- Archived original submission artifacts
- Repository bootstrap documentation
- GitHub issue and pull request templates
- Phase 1 planning baseline
- Phase 1 project scaffold and Docker Compose stack (`compose.yaml`, `compose.override.yaml`)
- Database roles, healthchecks, and backup/restore tooling under `infra/database` and `infra/deploy/scripts`
- Supabase storage client (`services/api/app/storage/`) with `StoredEvidence` dataclass and unit tests
- Runtime smoke script extension to upload/download evidence through the storage client
- `infra/deploy/scripts/backup-restore-smoke.sh` and `make backup-smoke` target for backup/restore validation
- `infra/deploy/docs/docker-operations.md` updated with backup-smoke procedure
- Phase 1 master tracker evidence entries for runtime smoke and backup/restore smoke runs
- HMAC-SHA256 verified `POST /payments/callback` endpoint for real payment-gateway integration with replay protection and idempotent transaction recording
- `services/api/app/services/payment_gateway.py` signature helper module
- `apply_gateway_callback` workflow plus shared `_record_payment_outcome` helper that writes audit log and `payment.settled` outbox event
- Unit tests for the HMAC signing helper and integration tests for the callback endpoint covering signed/unsigned, success, failure, and idempotent replay paths
- `docs/integrations/payment-callback.md` describing the gateway contract
- Unit tests for RBAC dependencies (`require_user`, `require_roles`), audit and outbox helpers, and the worker's `process_batch` and `update_heartbeat`
- Integration tests for the full violation lifecycle: report -> broadcast -> acknowledge -> stop outcome (admitted/disputed) -> complaint decide (confirm/revoke) -> simulated payment settlement
- Test suite expanded from 7 to 36 passing tests against the live Docker stack
- End-to-end test `tests/e2e/test_violation_lifecycle.py` that drives the full lifecycle through the HTTP API: officer login -> violation submission -> alert acknowledgement -> stop dispute -> complaint confirmation -> signed gateway payment callback -> paid state assertion
- `.github/workflows/ci.yml` GitHub Actions workflow that runs `ruff check`, `ruff format --check`, and the full `pytest` suite (unit + integration + e2e) inside the project's Docker Compose stack on every push to `main` and on every pull request
- `docs/api/endpoints.md` Phase 1 HTTP API reference enumerating every route, role requirement, form/body shape, response, and the workflow state machines
- `infra/deploy/docs/docker-operations.md` expanded with a production deployment runbook (host prep, secrets rotation, TLS, first boot, backups, monitoring, upgrades, rollback, scaling notes)
- `README.md` status block, key documents list, and local-operations section updated to reflect Phase 1 close-out and link the new API reference, payment callback contract, and deployment runbook

### Changed

- `pyproject.toml` ruff configuration: line length raised from 100 to 120 (modern industry standard), `flake8-bugbear` extended-immutable-calls list now exempts the FastAPI dependency-injection helpers (`Depends`, `Query`, `Header`, `Path`, `Body`, `Form`, `File`, `Cookie`, `Security`) and the project's own `require_user` / `require_roles` factories so the canonical FastAPI pattern stops triggering `B008`
- Entire `services/` and `tests/` trees reformatted by `ruff format` for consistency; `ruff check services tests` now reports zero issues

### Fixed

- `joinedload` queries against collection relationships in `/violations`, `/violations/{id}`, `/complaints`, and `/payments` now call `.unique()` on the result, fixing a latent SQLAlchemy `InvalidRequestError` raised when the routes returned violations, complaints, or payment requests with eager-loaded child rows
- `StorageClient.ensure_bucket` now recognises `supabase/storage-api` returning HTTP 400 with body `{"statusCode":"404","error":"Bucket not found"}` as a missing-bucket signal, so the bootstrap and runtime smoke create the evidence bucket on first boot instead of crashing with a 400
- `infra/deploy/scripts/backup-restore-smoke.sh` now calls `pg_restore --no-acl --no-owner` so the disposable validation database tolerates GRANTs against extension-provided functions (e.g. `graphql_public.graphql`) that are not pre-installed in the throwaway DB; the structural table-count check remains the success signal
