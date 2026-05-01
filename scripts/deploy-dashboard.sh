#!/usr/bin/env bash
# Безопасный деплой dashboard на сервер.
# Исключает .env, *.db, *.db-shm, *.db-wal — чтобы не затереть состояние сервера.
set -e

LOCAL_DIR="/Users/anton/FoodBusinesAcademy/apps/dashboard/"
REMOTE="fba:/opt/fba/vault/apps/dashboard/"

echo "→ Rsync dashboard → server (excluding env, dbs)..."
rsync -av \
  --exclude='.env' \
  --exclude='*.db' \
  --exclude='*.db-shm' \
  --exclude='*.db-wal' \
  --exclude='.omc/' \
  --exclude='__pycache__/' \
  "$LOCAL_DIR" "$REMOTE"

echo "→ Restarting fba-dashboard..."
ssh fba "systemctl restart fba-dashboard && sleep 1 && systemctl is-active fba-dashboard"
echo "✅ Deploy done. https://mistersushi36.pro"
