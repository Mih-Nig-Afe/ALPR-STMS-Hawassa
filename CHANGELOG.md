# Changelog

All notable changes to this repository will be documented in this file.

## [Unreleased]

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
