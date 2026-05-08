# PNP MR.SUSHI — Финансовый директор

Дашборд + Telegram-бот для PNL-учёта сети «Мистер Суши» (Воронеж).

## Состав
- **apps/dashboard/** — FastAPI дашборд + PNL таблица + ввод данных. URL: `findir.mistersushi36.pro`.
- **apps/findir-bot/** — Telegram-бот для ввода данных Антоном/управляющим.
- **deploy/** — systemd-юниты, nginx-конфиг, rsync-скрипты.
- **docs/** — схема PNL, флоу бота, ТЗ.

## Филиалы
1. Ростовская
2. 9 Января
3. Общие (агрегат двух)

## Роли
- `owner` (Антон) — видит всё: выручка, EBITDA, ЧП, ФОТ ФИО, налоги.
- `manager` (управляющий) — вносит данные. Скрыто: EBITDA, ЧП, ФОТ управляющих/маркетинга/бухгалтерии, налоги.

## Стек
Python 3.11+ · FastAPI · Jinja2 · SQLite · aiogram 3.x · bcrypt · Chart.js.

## Локальный запуск (тест)
```bash
cd apps/dashboard
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
DASHBOARD_SECRET=dev-secret uvicorn main:app --host 127.0.0.1 --port 8001 --reload
```
Открыть: http://localhost:8001/

## Деплой
```bash
./deploy/deploy-dashboard.sh
./deploy/deploy-bot.sh
```

## Налоговая система
АУСН 8% от оборота — вносится вручную как месячная статья.

## Метод учёта
Кассовый.
