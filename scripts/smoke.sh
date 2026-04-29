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

echo "Checking evidence upload and download"
docker compose exec -T api python - <<'PY'
from app.storage.client import StorageClient

payload = (
    b"\x89PNG\r\n\x1a\n"
    b"\x00\x00\x00\rIHDR"
    b"\x00\x00\x00\x01\x00\x00\x00\x01"
    b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
    b"\x00\x00\x00\nIDATx\x9cc`\x00\x00\x00\x02\x00\x01"
    b"\xe2!\xbc3"
    b"\x00\x00\x00\x00IEND\xaeB`\x82"
)
object_path = "smoke/evidence-smoke.png"

client = StorageClient()
stored = client.upload(object_path=object_path, content=payload, content_type="image/png")
downloaded, content_type = client.download(
    bucket_name=stored.bucket_name,
    object_path=stored.storage_key,
)

if downloaded != payload:
    raise SystemExit("downloaded evidence does not match uploaded evidence")
if "image/png" not in content_type:
    raise SystemExit(f"unexpected evidence content type: {content_type}")
PY

echo "Smoke checks passed"
