#!/usr/bin/env bash
#
# start.sh - per-boot startup for the Cursor Cloud Agent environment.
#
# Runs on every VM boot. The Docker daemon is a process and never survives
# into a new boot, so it (and the network fix) must be re-established here.
# Image builds and dependency installation belong in install.sh, not here.
set -euo pipefail

cd "$(dirname "$0")/../.."
REPO_ROOT="$(pwd)"
SCRIPTS="$REPO_ROOT/.cursor/scripts"

echo "==> Ensuring Docker is installed and running"
bash "$SCRIPTS/ensure-docker.sh"

echo "==> Ensuring .env exists"
[ -f .env ] || cp .env.example .env

echo "==> Starting the application stack"
docker compose up -d

echo "==> Waiting for the api container to become healthy"
"$SCRIPTS/wait-healthy.sh" api 240

# Migrations and seeding are idempotent; run them so a freshly booted pod
# (whose snapshot may predate a schema change) converges to head.
echo "==> Applying migrations and seed (idempotent)"
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.bootstrap

echo "start.sh completed. App available on http://localhost:8080"
