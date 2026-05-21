#!/usr/bin/env bash
set -euo pipefail

ROOT="/Users/medusa/Desktop/snap Extract"
HTML_PORT="${HTML_PORT:-8000}"
PROXY_PORT="${PROXY_PORT:-8765}"
HOST_BIND="${HOST_BIND:-0.0.0.0}"

cd "$ROOT"

mkdir -p "$ROOT/tmp"

pkill -f "python3 -m http.server ${HTML_PORT}" >/dev/null 2>&1 || true
pkill -f "python3 ${ROOT}/proxy.py" >/dev/null 2>&1 || true

nohup python3 -m http.server "${HTML_PORT}" --bind "${HOST_BIND}" \
  >"$ROOT/tmp/http_server.log" 2>&1 &

nohup env HOST="${HOST_BIND}" PORT="${PROXY_PORT}" python3 "$ROOT/proxy.py" \
  >"$ROOT/tmp/proxy_server.log" 2>&1 &

sleep 2

IP="$(ipconfig getifaddr en0 2>/dev/null || ipconfig getifaddr en1 2>/dev/null || true)"
if [[ -z "${IP}" ]]; then
  IP="$(ifconfig | awk '/inet / && $2 != "127.0.0.1" {print $2; exit}')"
fi

echo "HTML  : http://${IP}:${HTML_PORT}/snapextract_speed_demo.html"
echo "Proxy : http://${IP}:${PROXY_PORT}/health"
echo "Logs  : $ROOT/tmp/http_server.log"
echo "Logs  : $ROOT/tmp/proxy_server.log"
