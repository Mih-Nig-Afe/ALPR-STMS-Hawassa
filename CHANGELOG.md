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
