# ALPR-Based Smart Traffic Management System for Hawassa City

Manual-enforcement-first smart traffic management platform for Hawassa City, structured for phased delivery from Phase 1 digital reporting to future CCTV-assisted and ALPR-enabled enforcement.

## Status

- Repository bootstrap: complete
- Source artifact preservation: complete
- Phase 1 execution plan: complete
- Production implementation: not started

## Purpose

This repository formalizes the project foundation for the `ALPR STMS` initiative and prepares it for disciplined implementation, governance, and future GitHub collaboration.

The immediate target is **Phase 1**:
- manual digital violation reporting
- timestamp and GPS capture
- alert broadcasting
- complaint handling
- payment request initiation
- audit logging

The repository is intentionally structured so later phases can add CCTV ingestion, ALPR processing, and predictive intelligence without reorganizing the codebase.

## Repository Layout

```text
.
├── .github/                  GitHub issue and PR templates
├── apps/                     User-facing clients
│   ├── admin-web/
│   └── officer-pwa/
├── archive/                  Preserved original source artifacts
│   └── source-submission/
├── data/                     Seed and reference data
├── docs/                     Formal project documentation
│   ├── architecture/
│   ├── github/
│   ├── planning/
│   ├── product/
│   └── references/
├── infra/                    Database, deployment, and observability scaffolding
├── packages/                 Shared libraries and contracts
├── scripts/                  Automation scripts
├── services/                 Backend services
│   └── api/
└── tests/                    Unit, integration, and end-to-end tests
```

## Key Documents

- Project summary: [docs/product/project-summary.md](docs/product/project-summary.md)
- Repository structure guide: [docs/architecture/repository-structure.md](docs/architecture/repository-structure.md)
- Phase 1 execution plan: [docs/planning/phase-1-execution-plan.md](docs/planning/phase-1-execution-plan.md)
- GitHub metadata: [docs/github/repository-metadata.md](docs/github/repository-metadata.md)
- Source archive index: [docs/references/source-archive-index.md](docs/references/source-archive-index.md)

## Preserved Source Artifacts

The original academic and design artifacts are preserved under:

- [archive/source-submission/proposal](archive/source-submission/proposal)
- [archive/source-submission/guidelines](archive/source-submission/guidelines)
- [archive/source-submission/schedule](archive/source-submission/schedule)
- [archive/source-submission/references](archive/source-submission/references)
- [archive/source-submission/uml](archive/source-submission/uml)

These files are retained as the canonical submission baseline and should not be overwritten.

## Recommended Implementation Stack

- Backend: `FastAPI`
- Database: `PostgreSQL`
- Officer client: `PWA` first
- Office/admin client: responsive web app
- Maps: `OpenStreetMap`
- Storage: object-storage-compatible evidence repository
- Auth: RBAC with secure session management

## Governance Notes

- Keep Phase 1 scope strictly manual-enforcement-first.
- Do not reintroduce Phase 2 or Phase 3 features into the initial build.
- Treat the driver as an external payment participant, not an authenticated system user.
- Preserve auditability on every state-changing operation.

## Initial GitHub Position

- Suggested repository visibility: `Private`
- Suggested repository name: `alpr-stms-hawassa`
- Suggested topics and description: documented in [docs/github/repository-metadata.md](docs/github/repository-metadata.md)

## Next Implementation Step

Freeze the Phase 1 functional baseline, choose the implementation stack formally, and create the first backend and client services inside `services/api`, `apps/officer-pwa`, and `apps/admin-web`.
