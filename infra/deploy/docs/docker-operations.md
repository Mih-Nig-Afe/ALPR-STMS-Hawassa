# Docker Operations

## Local bootstrap

1. Copy `.env.example` to `.env`
2. Run `make up`
3. Open `http://localhost:8080`
4. Open MailHog at `http://localhost:8025`

## Core commands

- `make up`: build and start all services
- `make down`: stop the stack
- `make logs`: tail logs
- `make migrate`: run Alembic migrations
- `make seed`: run idempotent bootstrap data
- `make smoke`: run smoke validation
- `make backup`: create a database backup in the Docker backup volume
- `make backup-smoke`: create a backup and restore it into a temporary database

## Production posture

- use `.env.production` derived from `.env.production.example`
- place the reverse proxy behind TLS termination if the host already has a perimeter proxy
- store secrets outside the repository
- run backups on a schedule and export them off-host

## Backup and restore

Backups are written to the `db_backups` Docker volume as PostgreSQL custom-format dumps.

To create a backup:

```bash
make backup
```

To verify that a backup can be restored without touching the live database:

```bash
make backup-smoke
```

To restore a dump into the live database, stop dependent services first, then pass an absolute
host path to the dump:

```bash
docker compose stop api worker proxy supabase-storage supabase-rest
./infra/deploy/scripts/restore-db.sh /absolute/path/to/alpr-stms.dump
docker compose up -d
```

## Production deployment runbook

This section captures the steps required to bring a single-host production
deployment online. Phase 1 targets one Linux host (4 vCPU / 8 GB RAM minimum)
behind a TLS-terminating reverse proxy.

### 1. Prepare the host

- Install Docker Engine 26+ and the Compose plugin.
- Create a dedicated, unprivileged user for the application directory.
- Provision persistent disk for `db_data`, `storage_data`, and `db_backups`
  (the three named volumes declared in `compose.yaml`).
- Open inbound ports `80`/`443` only; everything else stays bound to loopback
  inside the Docker network.

### 2. Configure secrets

Copy `.env.production.example` to `.env` on the host (never commit `.env`):

```bash
cp .env.production.example .env
chmod 600 .env
```

Mandatory rotations before first boot:

| Variable | Notes |
| --- | --- |
| `APP_SECRET_KEY` | 64+ random bytes; used for cookie signing. |
| `POSTGRES_PASSWORD`, `DB_*_PASSWORD` | Distinct strong passwords per role. |
| `JWT_SECRET` | 32+ chars, shared between PostgREST and Storage. |
| `ANON_KEY`, `SERVICE_ROLE_KEY` | Re-issue with the new `JWT_SECRET`. |
| `PAYMENT_CALLBACK_SHARED_SECRET` | Coordinated with the gateway provider. |
| `OFFICER_DEFAULT_PASSWORD`, `ADMIN_DEFAULT_PASSWORD`, `COMPLAINT_DEFAULT_PASSWORD`, `SUBCITY_DEFAULT_PASSWORD` | Used only for the initial seed; rotate immediately after first login. |
| `S3_PROTOCOL_ACCESS_KEY_ID`, `S3_PROTOCOL_ACCESS_KEY_SECRET` | Random 32/64-char tokens. |

Set `APP_ENV=production`, `APP_DEBUG=false`, `APP_PUBLIC_URL=https://<your-domain>`,
and `SECURE_COOKIES=true`.

### 3. TLS termination

The bundled `proxy` service runs Caddy bound to port `80`. In production, place
the host behind a perimeter reverse proxy (Caddy / Nginx / Cloudflare) that
terminates TLS and forwards to `127.0.0.1:${APP_HTTP_PORT}`. The forwarded
proxy must set `X-Forwarded-Proto: https` so that secure-cookie behaviour
remains correct.

### 4. First boot

```bash
docker compose pull
docker compose build
docker compose up -d
make migrate
make seed
make smoke
```

The bootstrap seed (`python -m app.bootstrap`) is idempotent and may be
re-run after every upgrade.

### 5. Backups and disaster recovery

- Schedule `make backup` via cron or systemd-timer at least daily.
- Copy dumps off-host (object storage, off-site rsync) immediately after
  creation; the `db_backups` Docker volume alone is not a recovery target.
- Validate a dump weekly with `make backup-smoke`.
- Keep a 30-day rolling window plus monthly archival snapshots.

### 6. Monitoring and observability

- `GET /health/live` is a liveness probe; `GET /health/ready` performs a
  database round-trip and a Storage status call (returns `503` when storage
  is unreachable).
- Forward container logs (`docker compose logs --no-color`) into the host's
  log aggregator. The API and worker emit structured JSON.
- Audit any state mutation by tailing `audit_logs` (see `/admin` dashboard
  for the most recent 20 entries).

### 7. Upgrades

```bash
git fetch --tags && git checkout <release-tag>
docker compose pull
docker compose build api worker
docker compose up -d
make migrate
make smoke
```

If an upgrade introduces destructive migrations, take a `make backup` first
and announce maintenance.

### 8. Rollback

1. Restore the most recent verified dump (see Backup and restore above).
2. `git checkout <previous-tag>` and `docker compose up -d --build`.
3. Re-run `make smoke` to confirm the stack is healthy.

### 9. Scaling notes (Phase 1 scope)

Phase 1 is intentionally single-host. To scale read throughput, run the
`supabase-rest` and `supabase-storage` services on a second host and point
`POSTGREST_DATABASE_URL` / `STORAGE_DATABASE_URL` at the central database.
Horizontal scaling of the FastAPI service requires moving session storage
out of the local Postgres `sessions` table into a shared cache; this is
explicitly out of scope for Phase 1.
