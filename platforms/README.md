---
name: Platforms (FBA 2.0)
description: Три приоритетные площадки — TG, IG, YT. Остальные в .archive/platforms-v1/.
updated: 2026-04-27
---

# 📱 Platforms — FBA 2.0

| Платформа | URL | Режим |
|---|---|---|
| 🔷 [Telegram](telegram/format-rules.md) | https://t.me/Food_Busines_Academy | АВТО (Bot API) |
| 📸 [Instagram](instagram/format-rules.md) | https://instagram.com/mr.sushishef | Semi-auto |
| 📺 [YouTube](youtube/format-rules.md) | https://youtube.com/@Mistersushi36 | Semi-auto |

## Воронка

```
IG + YT  →  CTA →  TG (хаб)  →  leadmagnet-bot  →  PDF + подписка
```

## Структура папки платформы

```
platforms/<name>/
├── format-rules.md   ← правила формата (читает /draft skill)
├── calendar.md       ← редплан
└── published/        ← опубликованные материалы
    └── YYYY-MM-DD-slug.md
```

Архивированные площадки (VK, Dzen, Threads, MAX) → `.archive/platforms-v1/`
