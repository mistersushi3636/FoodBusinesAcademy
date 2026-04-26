---
name: Instagram Platform
description: Reels + карусели + Stories — визуальная экспертиза, CTA в Telegram
type: platform
priority: high
---

# 📸 Instagram — визуальная экспертиза

> Reels для охвата, карусели для сохранений, Stories для прогрева. CTA → ссылка в био → Telegram.

**Агент-стратег:** [[agents/platform/instagram|instagram-agent]]
**Аккаунт:** *(будет указан при запуске)*

---

## Структура папки

```
instagram/
├── README.md       ← этот файл
├── calendar.md     ← редплан Instagram
├── posts/          ← Reels, карусели, Stories
└── assets/         ← визуалы, обложки
```

---

## Текущий ритм

- **Reels:** 2–3/нед (15–90 сек)
- **Карусели:** 1–2/нед (5–10 слайдов)
- **Stories:** 3–5/нед
- Хэштеги: 5–10 целевых

---

## Готовые материалы

```dataview
TABLE WITHOUT ID
  file.link AS "Пост",
  format AS "Формат",
  publish_date AS "Дата",
  status AS "Статус"
FROM "platforms/instagram/posts"
SORT publish_date DESC
```

---

## Правила

См. [[agents/platform/instagram]] — форматы, хэштеги, CTA, запреты.
