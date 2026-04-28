# Contributing

## Working Rules

1. Preserve the original submission artifacts under `archive/source-submission/`.
2. Keep Phase 1 implementation strictly within the approved scope.
3. Do not mix future-phase features into the first production build.
4. Every workflow-affecting change must update the relevant document in `docs/`.
5. All state-changing backend actions must be auditable.

## Branching

- `main`: protected production-ready branch
- feature branches: `feature/<area>-<short-name>`
- fix branches: `fix/<area>-<short-name>`
- docs branches: `docs/<topic>`

## Pull Request Expectations

Every pull request should include:
- a clear problem statement
- the scope of the change
- testing performed
- documentation updates, if applicable
- explicit note if the change affects Phase 1 scope, violation states, RBAC, alerts, complaints, or payments

## Commit Style

Use short, explicit commit messages, for example:

- `docs: reorganize repository and preserve source artifacts`
- `api: add violation creation endpoint`
- `web: add officer login flow`
- `infra: add postgres compose profile`

## Documentation Discipline

Update these files whenever relevant:
- `README.md`
- `docs/product/project-summary.md`
- `docs/planning/phase-1-execution-plan.md`
- `docs/architecture/repository-structure.md`
- `docs/github/repository-metadata.md`
