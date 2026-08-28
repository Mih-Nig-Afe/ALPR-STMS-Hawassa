#!/usr/bin/env bash
#
# wait-healthy.sh <service> [timeout_seconds]
#
# Block until a docker compose service reports a healthy status, or fail
# with diagnostics after the timeout.
set -euo pipefail

SERVICE="${1:?usage: wait-healthy.sh <service> [timeout_seconds]}"
TIMEOUT="${2:-180}"

cd "$(dirname "$0")/../.."

deadline=$(( $(date +%s) + TIMEOUT ))
while true; do
  status=$(docker compose ps --format '{{.Service}} {{.Health}}' \
    | awk -v s="$SERVICE" '$1==s{print $2}' | head -n1)
  if [ "${status:-}" = "healthy" ]; then
    echo "    $SERVICE is healthy"
    break
  fi
  if [ "$(date +%s)" -ge "$deadline" ]; then
    echo "ERROR: $SERVICE did not become healthy within ${TIMEOUT}s (last: ${status:-unknown})" >&2
    docker compose ps
    docker compose logs --tail=50 "$SERVICE"
    exit 1
  fi
  sleep 3
done
