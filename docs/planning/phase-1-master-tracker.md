# Phase 1 Master Tracker

## 1. Project identity and dates

| Field | Value |
| --- | --- |
| Project | ALPR-Based Smart Traffic Management System for Hawassa City |
| Repository | `alpr-stms-hawassa` |
| Canonical tracker | `docs/planning/phase-1-master-tracker.md` |
| Phase in scope | Phase 1 only |
| Tracker effective date | 2026-04-29 |
| Current milestone | Production-ready repository formalization and Docker-first baseline |
| Baseline source archive | `archive/source-submission/` |
| Delivery model | Docker Compose on a single Linux host for local, staging, and initial production |

## 2. Locked technical decisions

| Area | Decision |
| --- | --- |
| Backend | Python `FastAPI` |
| Frontend | `Jinja2 + HTMX + Alpine.js + Bootstrap 5` with local vendor assets |
| Maps | `Leaflet` with OpenStreetMap tiles |
| Database | Self-hosted Supabase subset using `PostgreSQL + PostgREST + Storage API + imgproxy` |
| Auth | FastAPI-managed cookie sessions with RBAC |
| Worker model | Dedicated Python worker with database outbox polling |
| Deployment model | Docker Compose for local, staging, and single-host production |
| Evidence storage | Supabase Storage API with file backend for Phase 1 |
| Driver participation | External payment participant only, not an authenticated user |
| Language baseline | English-first, translation-ready structure |

## 3. Current repo health checklist

| Item | Status | Notes |
| --- | --- | --- |
| One canonical Phase 1 tracker exists | Complete | This file is canonical |
| Legacy plan paths point to canonical tracker | Complete | Root and historical path are pointer docs |
| README links resolve | Complete | Updated to canonical planning path |
| Repository hygiene workflow matches structure | Complete | Workflow now checks Docker and tracker assets |
| Docker entrypoint exists | Complete | `compose.yaml` and `compose.override.yaml` are required |
| Python project metadata exists | Complete | `pyproject.toml`, `requirements.in`, `requirements.lock` |
| Environment templates exist | Complete | Local, staging, and production examples |
| Runtime service scaffolds exist | Complete | API, worker, templates, and static assets are in place |
| Database migration baseline exists | Complete | Alembic baseline and seed payloads are in repository |
| Smoke verification recorded | Blocked | Docker daemon inactive on host prevented `compose up` validation |

## 4. Phase 1 scope lock

### Included

- officer authentication and RBAC
- manual violation capture
- GPS and timestamp capture
- evidence upload
- alert generation and acknowledgement
- complaint review and confirm/revoke flow
- payment request issuance and callback handling
- audit logging
- deployment, backup, and smoke validation

### Excluded

- CCTV ingestion
- ALPR/OCR processing
- automated ticket creation
- prediction engines
- external citizen portal
- multi-host orchestration and Kubernetes

## 5. Work breakdown table with task ID, status, owner, dependency, evidence, acceptance criteria

| Task ID | Work item | Status | Owner | Dependency | Evidence | Acceptance criteria |
| --- | --- | --- | --- | --- | --- | --- |
| P1-REP-001 | Establish canonical tracker and pointer documents | Complete | Codex | None | `docs/planning/*`, root pointer | One canonical tracker and no duplicated plan authority |
| P1-REP-002 | Repair README and repository hygiene workflow | Complete | Codex | P1-REP-001 | `README.md`, workflow file | Links and required path checks align with repository |
| P1-REP-003 | Add ADRs, Python metadata, env templates, and Makefile | Complete | Codex | P1-REP-002 | root config files, ADR docs | Repo has formal build, lint, and environment contracts |
| P1-INF-001 | Define Docker Compose baseline and local override | In progress | Codex | P1-REP-003 | `compose.yaml`, `compose.override.yaml` | Entire Phase 1 stack boots through Docker only |
| P1-INF-002 | Add reverse proxy and operational scripts | Complete | Codex | P1-INF-001 | `infra/deploy/` | Proxy routes UI, storage, and rest endpoints predictably |
| P1-DB-001 | Create initial schema and migration baseline | Complete | Codex | P1-INF-001 | Alembic files | All Phase 1 tables exist and migrate cleanly |
| P1-DB-002 | Create seed payloads and idempotent bootstrap flow | Complete | Codex | P1-DB-001 | `data/seed/`, bootstrap code | Local stack creates baseline roles, users, rules, and subcities |
| P1-AUTH-001 | Implement session auth and RBAC guards | Complete | Codex | P1-DB-001 | auth router and services | Users can log in, hold sessions, and be denied by role |
| P1-VIO-001 | Implement officer reporting workflow | Complete | Codex | P1-AUTH-001 | violations router, templates | Officer can submit a violation with GPS, time, and evidence |
| P1-ALT-001 | Implement alert generation and acknowledgement | Complete | Codex | P1-VIO-001 | alerts router, tables | Recipients receive and acknowledge alerts |
| P1-COM-001 | Implement complaint review workflow | Complete | Codex | P1-ALT-001 | complaints router and service | Complaint officer can confirm or revoke a disputed violation |
| P1-PAY-001 | Implement payment request and callback simulation | Complete | Codex | P1-COM-001 | payments router and service | Payment requests and status callbacks change violation state |
| P1-OPS-001 | Add backup, restore, and release runbooks | In progress | Codex | P1-INF-001 | `infra/deploy/docs`, scripts | Operators can back up and restore the database |
| P1-TST-001 | Add unit, integration, and smoke coverage | In progress | Codex | P1-AUTH-001 | `tests/` | Core workflows have automated checks |
| P1-TST-002 | Record validation evidence in tracker | Complete | Codex | P1-TST-001 | Section 11 updates | Tracker contains dated execution evidence |

## 6. Environment and secrets matrix

| Variable | Purpose | Environment | Rotation rule |
| --- | --- | --- | --- |
| `APP_SECRET_KEY` | FastAPI session and signing secret | All | Unique per environment, rotate before go-live |
| `POSTGRES_PASSWORD` | Postgres superuser and bootstrap role password | All | Unique per environment, store in secret manager |
| `JWT_SECRET` | PostgREST and Storage JWT verification secret | All | Unique outside local development |
| `ANON_KEY` | Supabase anon API key for self-hosted services | All | Derived from JWT secret for Phase 1 |
| `SERVICE_ROLE_KEY` | Service API key for storage and admin operations | All | Never expose to browser clients |
| `DB_APP_USER_PASSWORD` | FastAPI database login | All | Rotate per environment |
| `DB_WORKER_USER_PASSWORD` | Worker database login | All | Rotate per environment |
| `DB_STORAGE_USER_PASSWORD` | Storage service database login | All | Rotate per environment |
| `STORAGE_BUCKET` | Evidence bucket name | All | Stable once production starts |
| `SMTP_HOST` / `SMTP_PORT` | OTP and notification transport | All | Local uses MailHog, higher envs use real provider |
| `PAYMENT_CALLBACK_SHARED_SECRET` | Validates payment callbacks | All | Required before real gateway cutover |
| `MAP_TILE_URL` | OpenStreetMap tile endpoint | All | Override only if proxying tiles locally |

## 7. Docker services matrix

| Service | Source | Purpose | Ports | Health target | Persistent data |
| --- | --- | --- | --- | --- | --- |
| `proxy` | `caddy:2` | Public entrypoint and path routing | `8080 -> 80` | `GET /health/live` | No |
| `api` | Local Dockerfile | FastAPI UI, auth, workflows, and templates | internal `8000` | `GET /health/live` | No |
| `worker` | Local Dockerfile | Outbox processing and callback retries | internal | heartbeat file | No |
| `supabase-db` | `supabase/postgres` | Primary database | internal `5432` | `pg_isready` | `db_data`, `db_backups` |
| `supabase-rest` | `postgrest/postgrest` | REST gateway for DB-backed storage integration | internal `3000` | HTTP root | No |
| `supabase-storage` | `supabase/storage-api` | Evidence object storage API | internal `5000` | `GET /status` | `storage_data` |
| `supabase-imgproxy` | `darthsim/imgproxy` | Evidence image transformation | internal `5001` | built-in `imgproxy health` | `storage_data` |
| `mailhog` | `mailhog/mailhog` | Local SMTP and mail viewer | `8025 -> 8025`, `1025 -> 1025` | HTTP API | No |

## 8. Database schema checklist

| Table | Purpose | Status |
| --- | --- | --- |
| `roles` | RBAC catalog | In progress |
| `users` | System users | In progress |
| `subcities` | Operational geography | In progress |
| `officer_assignments` | User-to-subcity assignments | In progress |
| `violation_rules` | Enforceable rule definitions and penalties | In progress |
| `violations` | Primary violation records | In progress |
| `violation_evidence` | Evidence metadata and storage keys | In progress |
| `violation_alerts` | Alert bundles per violation | In progress |
| `alert_recipients` | Recipient state for alerts | In progress |
| `complaints` | Complaint cases | In progress |
| `complaint_decisions` | Complaint outcomes | In progress |
| `payment_requests` | Payment issuance records | In progress |
| `payment_transactions` | Callback and settlement events | In progress |
| `audit_logs` | Immutable activity trail | In progress |
| `outbox_events` | Worker-driven event handoff | In progress |
| `sessions` | Cookie session persistence | In progress |

## 9. API endpoint checklist

| Route group | Minimum endpoints | Status |
| --- | --- | --- |
| `/auth` | login, logout, session redirect | In progress |
| `/violations` | list, create, detail, stop outcome | In progress |
| `/alerts` | list, acknowledge | In progress |
| `/complaints` | list, decision | In progress |
| `/payments` | list, request, callback simulation | In progress |
| `/admin` | dashboard, users, rules, audit summary | In progress |
| `/health` | live and ready probes | In progress |

## 10. UI screen checklist

| Screen | Audience | Status |
| --- | --- | --- |
| Login | All authenticated users | In progress |
| Officer home | Traffic officer | In progress |
| Violation report form | Traffic officer | In progress |
| Alert inbox | Traffic officer / subcity officer | In progress |
| Complaint queue | Complaint officer | In progress |
| Payment queue | Complaint officer / admin | In progress |
| Admin dashboard | System administrator | In progress |
| Audit summary | System administrator | In progress |

## 11. Test execution log

| Date | Check | Status | Notes |
| --- | --- | --- | --- |
| 2026-04-29 | Repository structure review | Complete | Canonical tracker and Docker-first contract defined |
| 2026-04-29 | Python compile validation | Complete | `python3 -m compileall services/api services/worker packages/shared tests` |
| 2026-04-29 | App import validation | Complete | `PYTHONPATH=services/api:services/worker:packages/shared python3 -c "from app.main import app"` |
| 2026-04-29 | Unit and integration tests | Complete | `PYTHONPATH=services/api:services/worker:packages/shared python3 -m pytest tests/unit tests/integration -q` passed |
| 2026-04-29 | Compose static validation | Complete | `docker compose config` resolved successfully |
| 2026-04-29 | Runtime bootstrap validation | Blocked | Docker daemon inactive on host prevented `docker compose up` |
| 2026-04-29 | Backup and restore smoke | Pending | Scripts exist but not executed yet |

## 12. Risk and blocker register

| ID | Risk / blocker | Impact | Mitigation | Status |
| --- | --- | --- | --- | --- |
| R-001 | Scope leakage from future phases | High | Keep tracker scope lock and ADRs explicit | Active |
| R-002 | Storage API misconfiguration in self-hosted mode | High | Use official image contracts and local health checks | Active |
| R-003 | Missing gateway contract for real payments | Medium | Ship callback simulation first and isolate adapter layer | Active |
| R-004 | Weak operational discipline around tracker updates | Medium | Require tracker updates in every implementation change | Active |
| R-005 | Schedule pressure causes incomplete tests | High | Gate progress on smoke, auth, and workflow checks | Active |
| R-006 | Local Docker daemon inactive during verification | Medium | Start Docker and rerun `make up` and `make smoke` | Active |

## 13. Decision log

| Date | ID | Decision | Rationale |
| --- | --- | --- | --- |
| 2026-04-29 | D-001 | Keep Phase 1 limited to manual enforcement | Prevent design drift into CCTV and ALPR scope |
| 2026-04-29 | D-002 | Use FastAPI with server-rendered templates | Keeps stack Python-major and Docker-simple |
| 2026-04-29 | D-003 | Use self-hosted Supabase subset instead of Firebase Realtime DB | Docker-native self-hosting aligns with operational model |
| 2026-04-29 | D-004 | Use FastAPI-managed sessions rather than Supabase Auth | Phase 1 needs role-controlled internal users, not a separate auth platform |
| 2026-04-29 | D-005 | Use a worker and outbox pattern from the start | Preserves auditability and retries for alerts and payments |

## 14. Change log

| Date | Change |
| --- | --- |
| 2026-04-29 | Canonical tracker created |
| 2026-04-29 | Legacy plan paths demoted to pointer documents |
| 2026-04-29 | Repository formalization and Docker-first implementation approved |
| 2026-04-29 | FastAPI app, worker, Alembic baseline, seeds, vendor assets, and tests added |

## 15. Deployment readiness gate

| Gate | Required state | Status |
| --- | --- | --- |
| Documentation | Canonical tracker and ADRs updated | Complete |
| Configuration | Env templates complete | Complete |
| Runtime | Docker stack builds and becomes healthy | Blocked |
| Data | Migrations and seeds run cleanly | In progress |
| Security | Session auth, RBAC, secrets separation, callback secret | Complete |
| Evidence | Storage bucket reachable and upload path works | In progress |
| Audit | State transitions write audit logs | Complete |
| Testing | Smoke, unit, integration, and browser checks recorded | In progress |
| Operations | Backup and restore procedure verified | In progress |

## 16. Go-live signoff

| Role | Name | Date | Decision | Notes |
| --- | --- | --- | --- | --- |
| Product owner |  |  |  |  |
| Technical lead |  |  |  |  |
| Operations lead |  |  |  |  |
| Security reviewer |  |  |  |  |

## 17. Post-pilot findings

Record pilot findings here after first field deployment:

- observed workflow bottlenecks
- alert routing gaps
- evidence upload reliability
- complaint turnaround time
- payment callback issues
- data quality issues
