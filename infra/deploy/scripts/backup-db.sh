#!/usr/bin/env bash
set -euo pipefail

timestamp="$(date +%Y%m%d%H%M%S)"
filename="/backups/alpr-stms-${timestamp}.dump"

docker compose exec -T supabase-db sh -lc "pg_dump -U postgres -d \"\$POSTGRES_DB\" -Fc -f ${filename}"

echo "Backup created at ${filename} inside the db_backups Docker volume."

