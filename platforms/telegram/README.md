---
name: Telegram Platform
description: Главный хаб проекта — Telegram-канал Food Business Academy
type: platform
is_main_hub: true
---

# 🔷 Telegram — главный хаб

> Все остальные платформы ведут аудиторию сюда. Здесь: глубокая экспертиза, лид-магнит через бота, прогрев, продажи.

**Агент-стратег:** [[agents/platform/telegram|telegram-agent]]
**Канал:** *(будет указан при запуске)*
**Лид-магнит бот:** *(будет указан при запуске)*

---

## Структура папки

```
telegram/
├── README.md       ← этот файл
├── calendar.md     ← редплан Telegram
├── posts/          ← посты (по датам)
└── assets/         ← обложки и медиа
```

---

## Текущий ритм

- **3 поста/нед** на старте
- **Пн 08:30 · Ср 13:00 · Пт 19:30** (время МСК)
- Распределение пилларов по дням — см. [[agents/platform/telegram#Пилларовое распределение]]

---

## Готовые и опубликованные посты

```dataview
TABLE WITHOUT ID
  file.link AS "Пост",
  pillar AS "Пиллар",
  publish_date AS "Дата",
  status AS "Статус"
FROM "platforms/telegram/posts"
SORT publish_date DESC
```

---

## Правила поста

См. [[agents/platform/telegram]] — структура, хуки, CTA.
