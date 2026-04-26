---
name: VK Platform
description: Регионы и аудитория 30+ — посты, статьи, клипы, CTA в Telegram
type: platform
priority: secondary
---

# 🔵 ВКонтакте — регионы и 30+

> Региональная аудитория, возраст 30+. Длинные посты, статьи, клипы. CTA → Telegram.

**Агент-стратег:** [[agents/platform/vk|vk-agent]]
**Группа/страница:** *(будет указана при запуске)*

---

## Структура папки

```
vk/
├── README.md       ← этот файл
├── calendar.md     ← редплан ВК
├── posts/          ← посты и статьи
└── assets/         ← визуалы
```

---

## Текущий ритм

- **3–4 поста/нед**
- Посты до 15 000 символов
- Статьи для SEO-трафика
- Клипы = адаптация шортсов

---

## Готовые материалы

```dataview
TABLE WITHOUT ID
  file.link AS "Пост",
  pillar AS "Пиллар",
  publish_date AS "Дата",
  status AS "Статус"
FROM "platforms/vk/posts"
SORT publish_date DESC
```

---

## Правила

См. [[agents/platform/vk]] — форматы, SEO, CTA, запреты.
