#!/usr/bin/env bash
set -euo pipefail

APP_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE="brawlstars-ranked-helper"
HEALTH_URL="http://127.0.0.1:8000/health"
REQ_HASH_FILE="$APP_DIR/.requirements.hash"

cd "$APP_DIR"

echo "==> git pull"
git pull --ff-only origin master

hash_now="$(sha256sum requirements.txt | cut -d' ' -f1)"
hash_prev="$(cat "$REQ_HASH_FILE" 2>/dev/null || true)"

if [ "$hash_now" != "$hash_prev" ]; then
    echo "==> зависимости изменились: pip install -r requirements.txt"
    .venv/bin/pip install -r requirements.txt
    printf '%s\n' "$hash_now" > "$REQ_HASH_FILE"
else
    echo "==> зависимости не менялись, пропускаю pip install"
fi

echo "==> systemctl restart $SERVICE"
sudo systemctl restart "$SERVICE"

sleep 2

echo "==> healthcheck $HEALTH_URL"
if curl -fsS "$HEALTH_URL" 2>/dev/null | grep -q '"status":[[:space:]]*"ok"'; then
    echo "OK: приложение работает"
    systemctl status "$SERVICE" --no-pager -n 3 || true
else
    echo "ПРОВАЛ healthcheck. Последние строки журнала:"
    sudo journalctl -u "$SERVICE" -n 30 --no-pager || true
    exit 1
fi
