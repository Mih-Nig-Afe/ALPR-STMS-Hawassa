#!/usr/bin/env bash
#
# first-boot.sh
#
# One-shot bootstrap for a fresh ALPR STMS Hawassa host.
#
# Sequence:
#   1. Ensure .env exists (copies .env.example if missing).
#   2. Build and start the Docker Compose stack.
#   3. Wait for the api container to become healthy.
#   4. Run alembic migrations to head.
#   5. Seed reference data, roles, and default users.
#   6. Run the runtime smoke script (liveness, readiness, storage,
#      evidence upload + download round-trip).
#
# Safe to re-run: every step is idempotent.
set -euo pipefail

cd "$(dirname "$0")/../../.."

COMPOSE="docker compose"

echo "==> [1/6] Ensuring .env exists"
if [ ! -f .env ]; then
  if [ ! -f .env.example ]; then
    echo "ERROR: .env.example not found at repository root" >&2
    exit 1
  fi
  cp .env.example .env
  echo "    copied .env.example -> .env (rotate secrets before production use)"
else
  echo "    .env already present, leaving untouched"
fi

echo "==> [2/6] Building and starting the Docker Compose stack"
$COMPOSE up -d --build

echo "==> [3/6] Waiting for the api container to become healthy"
deadline=$(( $(date +%s) + 180 ))
while true; do
  status=$($COMPOSE ps --format '{{.Service}} {{.Health}}' \
    | awk '$1=="api"{print $2}' \
    | head -n1)
  if [ "${status:-}" = "healthy" ]; then
    echo "    api is healthy"
    break
  fi
  if [ "$(date +%s)" -ge "$deadline" ]; then
    echo "ERROR: api did not become healthy within 180s (last status: ${status:-unknown})" >&2
    $COMPOSE ps
    $COMPOSE logs --tail=50 api
    exit 1
  fi
  sleep 3
done

echo "==> [4/6] Running database migrations"
$COMPOSE run --rm api alembic upgrade head

echo "==> [5/6] Seeding reference data and default users"
$COMPOSE run --rm api python -m app.bootstrap

echo "==> [6/6] Running the runtime smoke script"
./scripts/smoke.sh

echo
echo "First-boot bootstrap completed successfully."
echo "Open the app at: http://localhost:8080"
echo "Default seeded accounts (passwords come from .env defaults):"
echo "  - traffic.officer1     (role: traffic_officer)"
echo "  - subcity.central      (role: subcity_officer)"
echo "  - complaints.officer   (role: complaint_officer)"
echo "  - sys.admin            (role: system_admin)"
