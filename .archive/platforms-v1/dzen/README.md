---
name: Dzen Platform
description: SEO-хвост — длинные статьи 5000–15000 символов, органический трафик из Яндекса
type: platform
priority: secondary
---

# 📰 Дзен — SEO-хвост

> Длинные экспертные статьи для органического трафика Яндекса. Долгосрочный актив. CTA → Telegram.

**Агент-стратег:** [[agents/platform/dzen|dzen-agent]]
**Канал:** *(будет указан при запуске)*

---

## Структура папки

```
dzen/
├── README.md       ← этот файл
├── calendar.md     ← редплан Дзен
├── articles/       ← статьи (SEO-оптимизированные)
└── assets/         ← обложки статей
```

---

## Текущий ритм

- **1–2 статьи/нед**
- Длина: 5 000–15 000 символов
- Ключевые слова в заголовке и подзаголовках
- Структура: введение → тело → вывод → CTA

---

## Готовые материалы

```dataview
TABLE WITHOUT ID
  file.link AS "Статья",
  pillar AS "Пиллар",
  publish_date AS "Дата",
  status AS "Статус"
FROM "platforms/dzen/articles"
SORT publish_date DESC
```

---

## Правила

См. [[agents/platform/dzen]] — SEO, структура, CTA, запреты.
