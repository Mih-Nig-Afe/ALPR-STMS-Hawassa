# ADR 002: Database and Storage Choice

## Status

Accepted on 2026-04-29.

## Context

Phase 1 needs a Docker-native, self-hostable database and evidence storage layer that fits a Python-major deployment and does not depend on a managed cloud runtime.

## Decision

Use a self-hosted Supabase subset for Phase 1:

- `supabase/postgres` for PostgreSQL
- `postgrest/postgrest` for DB-backed REST exposure where needed
- `supabase/storage-api` for evidence storage
- `darthsim/imgproxy` for image transformation

Do not use Firebase Realtime Database for this phase.

## Rationale

- Supabase publishes an official Docker-based self-hosting path for this operating model.
- Firebase Emulator Suite is for development and testing, not a production self-hosting target.
- The Phase 1 system benefits more from relational workflows, auditability, and transactional state changes than from document-style realtime sync.

## Consequences

### Positive

- PostgreSQL matches the workflow-heavy Phase 1 data model
- evidence storage remains colocated with the self-hosted stack
- deployment stays consistent across local, staging, and production

### Negative

- self-hosted storage configuration is more operationally involved than using a managed service
- the team must manage backups, secrets, and upgrades directly

## Follow-up

Use Supabase only for `PostgreSQL + Storage` in Phase 1. Defer Supabase Auth, Realtime, and Edge Functions until a later phase requires them.
