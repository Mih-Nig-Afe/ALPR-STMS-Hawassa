#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /absolute/path/to/backup.dump"
  exit 1
fi

backup_file="$1"
target_name="/tmp/restore.dump"

docker compose cp "${backup_file}" supabase-db:"${target_name}"
docker compose exec -T supabase-db sh -lc "pg_restore --clean --if-exists -U \"\${POSTGRES_USER:-supabase_admin}\" -d \"\$POSTGRES_DB\" ${target_name}"

echo "Restore completed from ${backup_file}."
