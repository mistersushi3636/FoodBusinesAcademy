#!/usr/bin/env bash
# Деплой findir-bot на сервер mistersushi36.pro
set -euo pipefail

LOCAL_DIR="/Users/anton/FoodBusinesAcademy/apps/findir-bot/"
REMOTE="fba:/opt/fba/vault/apps/findir-bot/"
SERVICE="findir-bot"

echo "→ Создаю каталоги на сервере..."
ssh fba "mkdir -p /opt/fba/vault/apps/findir-bot /opt/fba/venvs"

echo "→ Rsync bot → server..."
rsync -av \
    --exclude='.env' \
    --exclude='__pycache__/' \
    --exclude='.venv/' \
    --exclude='logs/' \
    "$LOCAL_DIR" "$REMOTE"

echo "→ Установка venv + зависимостей..."
ssh fba '
    cd /opt/fba/vault/apps/findir-bot
    if [ ! -d /opt/fba/venvs/findir-bot ]; then
        python3 -m venv /opt/fba/venvs/findir-bot
    fi
    /opt/fba/venvs/findir-bot/bin/pip install -q --upgrade pip
    /opt/fba/venvs/findir-bot/bin/pip install -q -r requirements.txt
'

echo "→ Установка systemd unit..."
scp /Users/anton/FoodBusinesAcademy/scripts/findir/findir-bot.service fba:/etc/systemd/system/${SERVICE}.service
ssh fba "systemctl daemon-reload && systemctl enable ${SERVICE} && systemctl restart ${SERVICE} && sleep 2 && systemctl is-active ${SERVICE}"

echo "✅ Bot deploy done."
