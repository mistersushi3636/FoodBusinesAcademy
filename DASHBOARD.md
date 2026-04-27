---
name: FBA 2.0 Dashboard
description: Главный командный центр Food Business Academy
version: 2.0
updated: 2026-04-27
---

```
╔══════════════════════════════════════════════════════════════╗
║              F B A   2 . 0   ·   D A S H B O A R D           ║
║                                                              ║
║  Voice → Post → Publish → Metrics · командный центр          ║
╚══════════════════════════════════════════════════════════════╝
```

> Один экран → весь проект. Минимализм, состояние, навигация.

## ▸ Production

- **Server:** `mistersushi36.pro` (168.222.140.43, Ubuntu 24.04, swtest.ru)
- **Bot anton-assistant:** `@your_assistant_bot` (личный, voice→post)
- **Bot leadmagnet:** `@your_leadmagnet_bot` (выдача PDF)
- **Dashboard URL:** https://mistersushi36.pro

## ▸ Площадки

| Платформа | URL | Режим публикации |
|---|---|---|
| Telegram | https://t.me/Food_Busines_Academy | **АВТО** через Bot API |
| Instagram | https://instagram.com/mr.sushishef | **Semi-auto** (бот → ЛС → ты) |
| YouTube | https://youtube.com/@Mistersushi36 | **Semi-auto** (бот → ЛС → ты) |

## ▸ Pipeline (state machine)

```
[idle]
  │ voice/text от Антона
  ↓
[captured]    /capture → идея в knowledge-base/transcripts/
  │
  ↓
[drafting]    /draft(platform) × N платформ параллельно
  │
  ↓
[visualizing] /visual → DALL-E картинка + Canva ТЗ
  │
  ↓
[reviewing]   /critique → проверка тон/факты/длина
  │
  ↓
[awaiting]    бот шлёт Антону превью + кнопки [Опубликовать / Правка / Отмена]
  │
  ↓
[publishing]  TG: авто; IG/YT: draft в ЛС
  │
  ↓
[learning]    /learn → метрики через 24/72/168ч → patterns/learnings.md
  │
  ↓
[done]
```

## ▸ Команда (7 skills, без агентов)

| Skill | Триггер | Output |
|---|---|---|
| `/capture` | voice/text | `knowledge-base/transcripts/{date}-{slug}.md` |
| `/draft` | idea + platform | `content/drafts/{date}-{platform}-{slug}.md` |
| `/visual` | draft | DALL-E image + `design-system/briefs/{slug}.md` |
| `/critique` | draft | inline review + edit |
| `/publish` | approved draft | TG API call OR personal message |
| `/plan` | cron Mon 11:00 | `content/plans/{YYYY-WW}-plan.md` |
| `/learn` | metrics ingest | append `patterns/learnings.md` |

## ▸ Стек

| Слой | Технология |
|---|---|
| LLM | Anthropic API (Claude Sonnet 4.6) + prompt caching |
| Image | OpenAI DALL-E 3 API |
| Voice | OpenAI Whisper API |
| Bot framework | aiogram 3 (asyncio) |
| State | SQLite (per-project) |
| Memory | `patterns/learnings.md` + SQLite vector index (если понадобится) |
| Dashboard | FastAPI + Jinja templates |
| Reverse proxy | nginx (на сервере, порты 80/443) |
| SSL | certbot (Let's Encrypt) |
| Process mgr | systemd (autorestart, on-boot) |
| Scheduler | systemd timer (Mon 11:00) |

## ▸ Брендовая база

- [brand/positioning.md](brand/positioning.md) — позиционирование
- [brand/audience.md](brand/audience.md) — 3 портрета ЦА
- [brand/tone-of-voice.md](brand/tone-of-voice.md) — голос
- `brand/examples/` — реальные посты Антона (нужно заполнить!)

## ▸ Пиллары (контент-рубрики)

| Пиллар | Доля | Описание |
|---|---|---|
| 💰 Деньги | 30% | маржа, юнит-экономика, чеки |
| ⚙️ Операционка | 20% | найм, КПИ, регламенты |
| 📣 Маркетинг | 20% | трафик, акции, упаковка |
| 📖 Кейсы | 20% | свои филиалы, ошибки, успехи |
| 🔮 Тренды | 10% | F&B новости, инструменты |

## ▸ Память

- [JOURNAL.md](JOURNAL.md) — решения и инсайты
- [patterns/learnings.md](patterns/learnings.md) — что зашло / не зашло (auto-update)
- [analytics/metrics/](analytics/metrics/) — метрики по неделям

## ▸ Что было до 2.0 (архив)

- `.archive/agents-v1/` — 18 .md ролей (orchestrator + 7 functional + 8 platform + 3 lead-magnets)
- `.archive/platforms-v1/` — VK, Dzen, Threads, MAX
- `.archive/skills-v1/` — старые 6 skills
- `.archive/meta-docs-v1/` — WORKSPACE, SYNC-SYSTEM, MOC, LAUNCH-CHECKLIST
- `.archive/bots-v1/` — стабы (ai-consultant, content-assistant, sales-bot)

**Почему ушло:** дублирование, нет рантайма, 8 платформ распыляли ресурсы. См. `JOURNAL.md` за 2026-04-27.

---

```
  ──────────────────────────────────────────────────────
  FBA 2.0 · anton@mistersushi36.pro · 2026-04-27
  ──────────────────────────────────────────────────────
```
