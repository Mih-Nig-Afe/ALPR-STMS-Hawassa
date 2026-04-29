# ALPR-Based Smart Traffic Management System for Hawassa City

Manual-enforcement-first traffic enforcement platform for Hawassa City, structured for phased delivery from Phase 1 field reporting to later CCTV-assisted and ALPR-enabled enforcement.

## Status

- Repository formalization: complete
- Docker-first runtime baseline: complete
- FastAPI service scaffold: complete
- Self-hosted Supabase subset: complete
- Phase 1 workflow tracker: closing out (see [`docs/planning/phase-1-master-tracker.md`](docs/planning/phase-1-master-tracker.md))
- Continuous integration: lint + structure check + pytest on every push and pull request

## Phase 1 Target

This repository is currently locked to **Phase 1** only:
- manual digital violation reporting
- GPS and timestamp capture
- alert broadcasting across subcity assignments
- complaint intake and review
- payment request initiation and callback handling
- audit logging on every state transition

Phase 1 explicitly excludes:
- live CCTV ingestion
- ALPR/OCR processing
- predictive routing
- automated violation generation

## Runtime Position

- Backend: `FastAPI`
- Frontend: `Jinja2 + HTMX + Alpine.js + Bootstrap 5` with local assets
- Database: self-hosted Supabase subset using `PostgreSQL + PostgREST + Storage API`
- Auth: FastAPI-managed cookie sessions with RBAC
- Maps: `OpenStreetMap` via `Leaflet`
- Packaging: Docker Compose for local, staging, and single-host production
- Background work: Python worker with a database outbox pattern

## Repository Layout

```text
.
├── .github/                  GitHub templates and repository checks
├── apps/                     Reserved client ownership boundaries
│   ├── admin-web/
│   └── officer-pwa/
├── archive/                  Preserved original source artifacts
├── data/                     Seed data and reference payloads
├── docs/                     Product, architecture, planning, and operations docs
├── infra/                    Database, deploy, and observability assets
├── packages/                 Shared Python utilities and contracts
├── scripts/                  Automation and smoke helpers
├── services/
│   ├── api/                  FastAPI application, templates, static assets
│   └── worker/               Background event processor
├── tests/                    Unit, integration, e2e, and smoke coverage
├── compose.yaml              Primary Docker orchestration entrypoint
└── compose.override.yaml     Local developer overlay
```

## Key Documents

- Project summary: [docs/product/project-summary.md](docs/product/project-summary.md)
- Repository structure: [docs/architecture/repository-structure.md](docs/architecture/repository-structure.md)
- Phase 1 master tracker: [docs/planning/phase-1-master-tracker.md](docs/planning/phase-1-master-tracker.md)
- Phase 1 execution pointer: [docs/planning/phase-1-execution-plan.md](docs/planning/phase-1-execution-plan.md)
- API reference: [docs/api/endpoints.md](docs/api/endpoints.md)
- Payment gateway callback contract: [docs/integrations/payment-callback.md](docs/integrations/payment-callback.md)
- Docker operations and production runbook: [infra/deploy/docs/docker-operations.md](infra/deploy/docs/docker-operations.md)
- ADR 001 stack decision: [docs/architecture/adr-001-phase1-stack.md](docs/architecture/adr-001-phase1-stack.md)
- ADR 002 database decision: [docs/architecture/adr-002-database-choice.md](docs/architecture/adr-002-database-choice.md)
- GitHub metadata: [docs/github/repository-metadata.md](docs/github/repository-metadata.md)
- Source archive index: [docs/references/source-archive-index.md](docs/references/source-archive-index.md)

## Preserved Source Artifacts

The original academic and design submission remains preserved under `archive/source-submission/`:

- [archive/source-submission/proposal](archive/source-submission/proposal)
- [archive/source-submission/guidelines](archive/source-submission/guidelines)
- [archive/source-submission/schedule](archive/source-submission/schedule)
- [archive/source-submission/references](archive/source-submission/references)
- [archive/source-submission/uml](archive/source-submission/uml)

These materials are archival references and should not be overwritten.

## Local Operations

1. Copy `.env.example` to `.env`
2. Build and start the stack with `make up`
3. Open `http://localhost:8080`
4. Run the test suite with `docker compose run --rm api pytest`
5. Review progress and acceptance gates in [docs/planning/phase-1-master-tracker.md](docs/planning/phase-1-master-tracker.md)

For a full production deployment walkthrough (secrets, TLS, backups, upgrade
and rollback procedures) see [`infra/deploy/docs/docker-operations.md`](infra/deploy/docs/docker-operations.md).

## Governance Notes

- Keep Phase 1 manual-enforcement-first.
- Treat the driver as an external payment participant, not an authenticated user.
- Record audit entries for every status mutation, decision, and payment event.
- Update the master tracker in every implementation change set.
