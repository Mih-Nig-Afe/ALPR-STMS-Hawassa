# Repository Structure

## Goal

This repository structure is designed to:
- preserve the original academic artifacts
- separate formal documentation from implementation
- support a future production codebase
- keep Phase 1 implementation clean and extensible

## Top-Level Directory Roles

### `.github/`

GitHub-facing operational files:
- issue templates
- pull request template

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
- `github/`: GitHub setup metadata
- `planning/`: execution and delivery planning
- `product/`: scope and business-level summaries
- `references/`: indexes to preserved source materials

### `apps/`

User-facing clients.

Planned use:
- `apps/officer-pwa`: field officer workflow client
- `apps/admin-web`: office/admin/subcity web client

### `services/`

Backend services.

Planned use:
- `services/api`: primary Phase 1 backend

### `packages/`

Shared code, contracts, or utilities reused across clients and services.

### `infra/`

Operational scaffolding:
- database setup
- deployment assets
- observability

### `data/`

Seed data, controlled import files, and reference datasets.

### `scripts/`

Automation scripts for setup, migration, validation, or release tasks.

### `tests/`

Formal test boundaries:
- unit
- integration
- e2e

## Structural Rules

1. Preserve archive materials exactly.
2. Keep active implementation out of `docs/` and `archive/`.
3. Keep backend logic inside `services/`.
4. Keep shared schemas or contracts inside `packages/`.
5. Keep operational configuration under `infra/`.
6. Keep feature growth aligned with the documented phase model.
