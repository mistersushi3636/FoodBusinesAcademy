#!/usr/bin/env bash
# Первичная установка findir на сервере: nginx + TLS + .env
set -euo pipefail

echo "→ Загружаем nginx config..."
scp /Users/anton/FoodBusinesAcademy/scripts/findir/nginx-findir.conf fba:/etc/nginx/sites-available/findir.mistersushi36.pro

ssh fba '
    set -e
    ln -sf /etc/nginx/sites-available/findir.mistersushi36.pro /etc/nginx/sites-enabled/findir.mistersushi36.pro

    touch /opt/fba/.env
    chmod 600 /opt/fba/.env
    grep -q "^DASHBOARD_API_KEY=" /opt/fba/.env || echo "DASHBOARD_API_KEY=$(openssl rand -hex 32)" >> /opt/fba/.env
    grep -q "^DASHBOARD_SECRET=" /opt/fba/.env || echo "DASHBOARD_SECRET=$(openssl rand -hex 32)" >> /opt/fba/.env
    grep -q "^DASHBOARD_DB_PATH=" /opt/fba/.env || echo "DASHBOARD_DB_PATH=/opt/fba/vault/data/findir.db" >> /opt/fba/.env
    grep -q "^DASHBOARD_API_URL=" /opt/fba/.env || echo "DASHBOARD_API_URL=http://127.0.0.1:8002" >> /opt/fba/.env
    grep -q "^OWNER_USERNAME=" /opt/fba/.env || echo "OWNER_USERNAME=anton" >> /opt/fba/.env
    grep -q "^OWNER_PASSWORD=" /opt/fba/.env || echo "OWNER_PASSWORD=CHANGE_ME" >> /opt/fba/.env
    grep -q "^MANAGER_USERNAME=" /opt/fba/.env || echo "MANAGER_USERNAME=manager" >> /opt/fba/.env
    grep -q "^MANAGER_PASSWORD=" /opt/fba/.env || echo "MANAGER_PASSWORD=CHANGE_ME" >> /opt/fba/.env
    grep -q "^FINDIR_BOT_TOKEN=" /opt/fba/.env || echo "FINDIR_BOT_TOKEN=CHANGE_ME" >> /opt/fba/.env
    grep -q "^OWNER_TG_ID=" /opt/fba/.env || echo "OWNER_TG_ID=0" >> /opt/fba/.env
    grep -q "^MANAGER_TG_ID=" /opt/fba/.env || echo "MANAGER_TG_ID=0" >> /opt/fba/.env

    if ! [ -d /etc/letsencrypt/live/findir.mistersushi36.pro ]; then
        certbot --nginx -d findir.mistersushi36.pro --non-interactive --agree-tos -m mistersushi3636@gmail.com || true
    fi

    nginx -t && systemctl reload nginx
'

echo "✅ Базовая установка завершена."
echo "Дальше:"
echo "  1) Заполни /opt/fba/.env — OWNER_PASSWORD, MANAGER_PASSWORD, FINDIR_BOT_TOKEN, OWNER_TG_ID, MANAGER_TG_ID"
echo "  2) ssh fba 'systemctl restart findir-dashboard findir-bot'"
echo "  3) Открой https://findir.mistersushi36.pro"
