#!/usr/bin/env bash
set -euo pipefail

timestamp="$(date +%Y%m%d%H%M%S)"
backup_file="/backups/alpr-stms-smoke-${timestamp}.dump"
restore_db="restore_smoke_${timestamp}"

cleanup() {
  docker compose exec -T supabase-db sh -lc "dropdb -U \"\${POSTGRES_USER:-supabase_admin}\" \"${restore_db}\" 2>/dev/null || true" >/dev/null
}
trap cleanup EXIT

docker compose exec -T supabase-db sh -lc "pg_dump -U \"\${POSTGRES_USER:-supabase_admin}\" -d \"\$POSTGRES_DB\" -Fc -f \"${backup_file}\""
docker compose exec -T supabase-db sh -lc "createdb -U \"\${POSTGRES_USER:-supabase_admin}\" \"${restore_db}\""
docker compose exec -T supabase-db sh -lc "pg_restore -U \"\${POSTGRES_USER:-supabase_admin}\" -d \"${restore_db}\" \"${backup_file}\""

table_count="$(
  docker compose exec -T supabase-db sh -lc "psql -U \"\${POSTGRES_USER:-supabase_admin}\" -d \"${restore_db}\" -Atc \"select count(*) from information_schema.tables where table_schema in ('public', 'storage');\""
)"

if [[ "${table_count}" -le 0 ]]; then
  echo "Restore smoke failed: restored database has no public/storage tables"
  exit 1
fi

echo "Backup and restore smoke passed with ${table_count} restored public/storage tables."
