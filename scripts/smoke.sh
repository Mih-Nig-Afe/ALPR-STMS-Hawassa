#!/usr/bin/env bash
###
 # @Author: Mih-Nig-Afe 90252194+Mih-Nig-Afe@users.noreply.github.com
 # @Date: 2026-04-29 12:53:30
 # @LastEditors: Mih-Nig-Afe 90252194+Mih-Nig-Afe@users.noreply.github.com
 # @LastEditTime: 2026-05-03 18:18:49
 # @FilePath: /ALPR STMS Hawassa/scripts/smoke.sh
 # @Description: 这是默认设置,请设置`customMade`, 打开koroFileHeader查看配置 进行设置: https://github.com/OBKoro1/koro1FileHeader/wiki/%E9%85%8D%E7%BD%AE
### 
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

echo "Checking proxy login page render"
login_html=$(curl -fsS http://localhost:8080/auth/login)
if ! grep -q "ALPR STMS Hawassa Login" <<<"$login_html"; then
  echo "ERROR: /auth/login did not render the expected title" >&2
  exit 1
fi
if ! grep -q '<form' <<<"$login_html"; then
  echo "ERROR: /auth/login did not render a login form" >&2
  exit 1
fi

echo "Smoke checks passed"
