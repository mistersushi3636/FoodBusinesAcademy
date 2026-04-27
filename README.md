---
name: FBA 2.0 — Food Business Academy
description: Личный бренд Антона Коваленко. Voice → Post → Publish → Metrics конвейер.
version: 2.0
updated: 2026-04-27
---

# 🍱 Food Business Academy 2.0

Экспертный личный бренд Антона Коваленко (Воронеж, «Мистер Суши», 13 лет в ресторанном бизнесе).

**ЦА:** рестораторы, основатели доставок, повара с предпринимательскими амбициями.
**Площадки (фокус):** Telegram • Instagram • YouTube.
**Миссия:** реальный опыт без инфоцыганщины — конкретные цифры, кейсы, рабочие решения.

## 🚀 Старт

→ **[DASHBOARD.md](DASHBOARD.md)** — главный экран проекта.
→ **[JOURNAL.md](JOURNAL.md)** — память проекта (решения, инсайты).

## 📂 Структура

| Папка | Назначение |
|---|---|
| `brand/` | Позиционирование, аудитория, тон голоса, реальные примеры постов |
| `patterns/` | `learnings.md` — что зашло, что нет (растёт со временем) |
| `platforms/{telegram,instagram,youtube}/` | Правила форматов + календари + готовый контент |
| `content/` | Идеи, черновики, опубликованное |
| `content-bank/` | Ядра контента по форматам (text, short-video, long-video, visual) |
| `knowledge-base/` | Транскрипты голосовых, разборы конкурентов, FAQ, кейсы |
| `products/` | Курсы, консультации, лид-магниты |
| `analytics/metrics/` | Метрики по неделям |
| `design-system/` | Бренд-визуал + AI-промпты |
| `apps/` | Код проекта (боты, dashboard, shared lib) |
| `.claude/skills/` | 7 skills нового pipeline |

## 🤖 Apps

- `apps/anton-assistant/` — личный TG-бот Антона: voice → idea → draft → review → publish
- `apps/leadmagnet-bot/` — выдаёт PDF за подписку на канал
- `apps/dashboard/` — веб-дашборд (FastAPI), доступен на mistersushi36.pro
- `apps/shared/` — клиенты Anthropic/OpenAI/Whisper/Telegram/IG/YT + memory

## 🔄 Pipeline (V3 — state machine)

```
voice → /capture → idea
idea → /draft(platform) → post_draft
post_draft → /visual → image_brief + DALL-E
post_draft + image → /critique → review
review → Антон approves → /publish
publish → /learn(metrics) → patterns/learnings.md
```

## 📅 Еженедельный цикл

Понедельник 11:00 (systemd timer на сервере) → `/plan`:
- Читает `analytics/metrics/`
- Запускает `competitor-parser`
- Self-critique
- Сохраняет 30-дневный план
- Пингует Антона в TG с summary

## 🛠 Skills (7 штук вместо 18 агентов)

| Skill | Делает |
|---|---|
| `/capture` | voice/text → структурированная идея |
| `/draft` | idea + platform → пост |
| `/visual` | пост → DALL-E промпт + Canva ТЗ |
| `/critique` | review поста (тон, факты, длина) |
| `/publish` | TG: автопост; IG/YT: draft в личку Антону |
| `/plan` | еженедельный цикл (metrics → 30d plan) |
| `/learn` | metrics → инсайты → patterns/learnings.md |

## 📜 История

Старая структура (18 агентов, 8 платформ, дублирующиеся meta-docs) → `.archive/`.
