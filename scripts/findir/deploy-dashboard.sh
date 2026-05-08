#!/usr/bin/env bash
# Деплой findir-dashboard на сервер mistersushi36.pro (SSH alias: fba)
set -euo pipefail

LOCAL_DIR="/Users/anton/FoodBusinesAcademy/apps/findir-dashboard/"
REMOTE="fba:/opt/fba/vault/apps/findir-dashboard/"
SERVICE="findir-dashboard"

echo "→ Создаю каталоги на сервере..."
ssh fba "mkdir -p /opt/fba/vault/apps/findir-dashboard /opt/fba/vault/data /opt/fba/venvs"

echo "→ Rsync dashboard → server (без .env, *.db, .venv)..."
rsync -av \
    --exclude='.env' \
    --exclude='*.db' \
    --exclude='*.db-shm' \
    --exclude='*.db-wal' \
    --exclude='__pycache__/' \
    --exclude='.venv/' \
    "$LOCAL_DIR" "$REMOTE"

echo "→ Установка venv + зависимостей..."
ssh fba '
    cd /opt/fba/vault/apps/findir-dashboard
    if [ ! -d /opt/fba/venvs/findir-dashboard ]; then
        python3 -m venv /opt/fba/venvs/findir-dashboard
    fi
    /opt/fba/venvs/findir-dashboard/bin/pip install -q --upgrade pip
    /opt/fba/venvs/findir-dashboard/bin/pip install -q -r requirements.txt
'

echo "→ Установка systemd unit..."
scp /Users/anton/FoodBusinesAcademy/scripts/findir/findir-dashboard.service fba:/etc/systemd/system/${SERVICE}.service
ssh fba "systemctl daemon-reload && systemctl enable ${SERVICE} && systemctl restart ${SERVICE} && sleep 2 && systemctl is-active ${SERVICE}"

echo "✅ Dashboard deploy done. URL: https://findir.mistersushi36.pro"
