---
name: Threads Platform
description: Короткие касания — 500 символов, 5–7 постов/нед, CTA в Telegram
type: platform
priority: secondary
---

# 🧵 Threads — короткие касания

> Короткие мысли, провокации, инсайты. 500 симв. Частота = присутствие. CTA → Telegram.

**Агент-стратег:** [[agents/platform/threads|threads-agent]]
**Аккаунт:** *(будет указан при запуске)*

---

## Структура папки

```
threads/
├── README.md       ← этот файл
├── calendar.md     ← редплан Threads
├── posts/          ← тексты постов
└── assets/         ← медиа (опционально)
```

---

## Текущий ритм

- **5–7 постов/нед**
- До 500 символов
- Треды (цепочки) для развёрнутых мыслей
- Без хэштегов

---

## Готовые материалы

```dataview
TABLE WITHOUT ID
  file.link AS "Пост",
  pillar AS "Пиллар",
  publish_date AS "Дата",
  status AS "Статус"
FROM "platforms/threads/posts"
SORT publish_date DESC
```

---

## Правила

См. [[agents/platform/threads]] — формат, тон, CTA.
