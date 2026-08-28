#!/usr/bin/env bash
#
# install.sh - repository bootstrap for the Cursor Cloud Agent environment.
#
# Durable, idempotent setup that can be baked into an environment build:
#   1. Ensure a working Docker daemon (see ensure-docker.sh).
#   2. Create .env from the checked-in example.
#   3. Build the api/worker images and pull service images.
#   4. Bring the stack up once, migrate, and seed so the database volume
#      and images are captured in the environment snapshot.
set -euo pipefail

cd "$(dirname "$0")/../.."
REPO_ROOT="$(pwd)"
SCRIPTS="$REPO_ROOT/.cursor/scripts"

echo "==> [1/5] Ensuring Docker is installed and running"
bash "$SCRIPTS/ensure-docker.sh"

echo "==> [2/5] Ensuring .env exists"
if [ ! -f .env ]; then
  cp .env.example .env
  echo "    copied .env.example -> .env"
else
  echo "    .env already present"
fi

echo "==> [3/5] Building images and pulling service images"
docker compose build
docker compose up -d

echo "==> [4/5] Waiting for the api container to become healthy"
"$SCRIPTS/wait-healthy.sh" api 240

echo "==> [5/5] Running migrations and seeding reference data"
docker compose run --rm api alembic upgrade head
docker compose run --rm api python -m app.bootstrap

echo "install.sh completed successfully."
