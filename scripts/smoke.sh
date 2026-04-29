#!/usr/bin/env bash
set -euo pipefail

echo "Checking docker compose service state"
docker compose ps

echo "Checking application liveness"
curl -fsS http://localhost:8080/health/live >/dev/null

echo "Checking application readiness"
curl -fsS http://localhost:8080/health/ready >/dev/null

echo "Checking storage health"
curl -fsS http://localhost:15000/status >/dev/null

echo "Smoke checks passed"

