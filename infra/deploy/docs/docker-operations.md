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
