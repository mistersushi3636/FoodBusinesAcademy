---
name: YouTube Platform
description: Глубокая экспертиза — длинные видео + Shorts, 1 видео = источник для 3–5 Shorts
type: platform
priority: high
---

# 📺 YouTube — глубокая экспертиза

> Длинные видео (5–30 мин) для доверия. Shorts для охвата. 1 видео → 3–5 Shorts + адаптации. CTA → Telegram.

**Агент-стратег:** [[agents/platform/youtube|youtube-agent]]
**Канал:** *(будет указан при запуске)*

---

## Структура папки

```
youtube/
├── README.md       ← этот файл
├── calendar.md     ← редплан YouTube
├── videos/         ← сценарии длинных видео
│   └── shorts/     ← сценарии Shorts
└── assets/         ← превью, заставки
```

---

## Текущий ритм

- **Длинные:** 1/нед (вт или чт, 18:00 МСК)
- **Shorts:** 2–3/нед из длинных
- Превью: лицо + цифра/вопрос

---

## Готовые материалы

```dataview
TABLE WITHOUT ID
  file.link AS "Видео",
  format AS "Формат",
  publish_date AS "Дата",
  status AS "Статус"
FROM "platforms/youtube/videos"
SORT publish_date DESC
```

---

## Правила

См. [[agents/platform/youtube]] — структура, превью, SEO, CTA.
