#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

PORT="${APP_HTTP_PORT:-8080}"

echo "[1/3] Starting stack..."
docker compose up -d

echo "[2/3] Starting ngrok tunnel on port ${PORT}..."
if ! command -v ngrok >/dev/null 2>&1; then
  echo "ngrok not found. Install ngrok first: https://ngrok.com/download"
  exit 1
fi
ngrok http "${PORT}" --log=stdout > /tmp/alpr-ngrok.log 2>&1 &
NGROK_PID=$!
trap 'kill ${NGROK_PID} >/dev/null 2>&1 || true' EXIT

echo "[3/3] Waiting for ngrok public URL..."
PUBLIC_URL=""
for _ in {1..20}; do
  sleep 1
  PUBLIC_URL="$(curl -s http://127.0.0.1:4040/api/tunnels | python3 -c 'import json,sys; d=json.load(sys.stdin); print(next((t["public_url"] for t in d.get("tunnels", []) if t.get("proto") == "https"), ""))')"
  if [[ -n "${PUBLIC_URL}" ]]; then
    break
  fi
done
if [[ -z "${PUBLIC_URL}" ]]; then
  echo "Could not fetch ngrok URL. Check /tmp/alpr-ngrok.log"
  exit 1
fi

echo "ALPR STMS public test URL: ${PUBLIC_URL}"
echo "Share this URL with test devices. Press Ctrl+C to stop ngrok."
wait "${NGROK_PID}"
