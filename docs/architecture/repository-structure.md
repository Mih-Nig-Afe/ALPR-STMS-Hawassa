# Repository Structure

## Goal

This repository structure is designed to:
- preserve the original academic artifacts
- separate formal documentation from implementation
- support a formal Docker-first production codebase
- keep Phase 1 implementation clean, testable, and extensible

## Top-Level Directory Roles

### `.github/`

GitHub-facing operational files:
- issue templates
- pull request template
- repository hygiene workflow

### `archive/`

Immutable source archive of the original submission package.

Use this for:
- reference
- traceability
- examiner comparison

Do not use it for active implementation files.

### `docs/`

Maintained project documentation.

Subsections:
- `architecture/`: repo and system structure decisions
- `github/`: GitHub setup metadata and conventions
- `planning/`: the canonical Phase 1 tracker and execution aliases
- `product/`: scope and business-level summaries
- `references/`: indexes to preserved source materials

### `apps/`

User-facing clients.

These directories remain as ownership boundaries for future extraction. In Phase 1, the actual UI is served by the FastAPI service through server-rendered templates.

- `apps/officer-pwa`: reserved ownership boundary for future officer client extraction
- `apps/admin-web`: reserved ownership boundary for future admin client extraction

### `services/`

Backend services.

Active use:
- `services/api`: primary Phase 1 FastAPI application, templates, static assets, domain logic, and migrations entrypoint
- `services/worker`: background worker for outbox processing, callback retries, and operational jobs

### `packages/`

Shared Python code, enums, and utilities reused across services.

### `infra/`

Operational scaffolding:
- `database/`: Alembic migrations, bootstrap helpers, backup scripts
- `deploy/`: Docker, reverse proxy, and release runbooks
- `observability/`: reserved metrics and dashboard configuration

### `data/`

Seed data, controlled import payloads, and reference datasets.

- `data/seed/sql`: SQL bootstrap payloads
- `data/seed/json`: application-level seed records

### `scripts/`

Automation scripts for setup, validation, and smoke operations.

### `tests/`

Formal test boundaries:
- unit
- integration
- e2e
- smoke

## Structural Rules

1. Preserve archive materials exactly.
2. Keep active implementation out of `docs/` and `archive/`.
3. Keep backend logic inside `services/api` and background jobs inside `services/worker`.
4. Keep shared contracts inside `packages/`.
5. Keep operational configuration under `infra/`.
6. Keep all runtime paths reproducible through Docker Compose.
7. Keep `docs/planning/phase-1-master-tracker.md` as the single canonical execution record.
8. Keep feature growth aligned with the documented phase model.
