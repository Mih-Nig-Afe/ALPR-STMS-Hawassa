# ADR 001: Phase 1 Stack

## Status

Accepted on 2026-04-29.

## Context

Phase 1 needs a small operational footprint, strong auditability, and a Python-first implementation path that can run consistently in local, staging, and initial production without adding a second application platform.

## Decision

Use the following stack for Phase 1:

- `FastAPI` for the backend application
- server-rendered UI with `Jinja2`, `HTMX`, `Alpine.js`, and `Bootstrap 5`
- `Leaflet` with OpenStreetMap tiles for location capture and escape path review
- cookie-session auth with RBAC handled by FastAPI
- Docker Compose as the single runtime entrypoint
- a dedicated Python worker for asynchronous event processing

## Consequences

### Positive

- one major language across app and worker
- low operational overhead for a single-host deployment
- templates and HTMX keep the officer and admin flows fast to build
- easier audit logging because state mutations stay close to the server

### Negative

- server-rendered UI is less flexible than a separate SPA if product scope expands quickly
- a single service boundary means the API owns both UI delivery and domain workflows in Phase 1

## Follow-up

If a future phase requires a separate client application, extract the officer or admin surface into `apps/` without changing the domain and database boundaries established in `services/api`.

