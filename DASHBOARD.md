---
name: Dashboard
description: Главный дашборд Food Business Academy — процессы, статусы, метрики всех платформ
type: dashboard
updated: 2026-04-21
---

```
 ┌─────────────────────────────────────────────────────────────┐
 │                                                             │
 │        F O O D    B U S I N E S S    A C A D E M Y          │
 │                                                             │
 │              Command center · мониторинг процессов          │
 │                                                             │
 └─────────────────────────────────────────────────────────────┘
```

> Одна страница → вся картина проекта. Минимализм, данные, навигация.

---

## ▸ Навигация

|  |  |  |
|---|---|---|
| 🤖 [Agents](agents/README.md) | 🎨 [Design System](design-system/README.md) | 💎 [Lead Magnets](agents/lead-magnets/README.md) |
| 📱 [Platforms](platforms/) | 📦 [Content Bank](content-bank/) | 📓 [Journal](JOURNAL.md) |
| 🎭 [Brand](brand/) | 📚 [Knowledge Base](knowledge-base/) | 🗺️ [MOC](MOC.md) |

---

## ▸ Текущая фаза

```
Запуск · 90 дней · Неделя 1 из 13
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
██░░░░░░░░░░░░░░░░░░░░░░░░░░   8%
```

**Фокус недели:** инфраструктура агентов · первые 3 поста TG · пилот Shorts

---

## ▸ Команда агентов — статус

### 🎯 Core

| Агент | Роль | Статус |
|---|---|---|
| [orchestrator](agents/orchestrator.md) | Координатор | ✅ Активен |

### ⚙️ Functional

| Агент | Роль | Статус |
|---|---|---|
| [content-adapter](agents/functional/content-adapter.md) | Адаптация источников | ✅ Активен |
| [research](agents/functional/research.md) | Разведка | ✅ Активен |
| [calendar](agents/functional/calendar.md) | Редплан | ✅ Активен |
| [analytics](agents/functional/analytics.md) | Метрики + обучение | ✅ Активен |
| [designer](agents/functional/designer.md) | Визуал | ✅ Активен |
| [editor](agents/functional/editor.md) | Вычитка | ✅ Активен |

### 📱 Platform

| Агент | Платформа | Статус |
|---|---|---|
| [telegram](agents/platform/telegram.md) | 🔷 Telegram (HUB) | 🟢 Приоритет |
| [tiktok](agents/platform/tiktok.md) | 🎵 TikTok | 🟢 Приоритет |
| [instagram](agents/platform/instagram.md) | 📸 Instagram | 🟢 Приоритет |
| [youtube](agents/platform/youtube.md) | 📺 YouTube | 🟢 Приоритет |
| [vk](agents/platform/vk.md) | 🔵 ВКонтакте | 🟡 Вторично |
| [dzen](agents/platform/dzen.md) | 📰 Дзен | 🟡 Вторично |
| [threads](agents/platform/threads.md) | 🧵 Threads | 🟡 Вторично |
| [max](agents/platform/max.md) | 💬 MAX | ⚪ Зеркало |

### 💎 Lead Magnets

| Агент | Этап | Статус |
|---|---|---|
| [researcher](agents/lead-magnets/researcher.md) | 1 — исследование | ✅ Активен |
| [architect](agents/lead-magnets/architect.md) | 2 — концепция | ✅ Активен |
| [producer](agents/lead-magnets/producer.md) | 3 — производство | ✅ Активен |

---

## ▸ Воронка

```
 TikTok · YT · Reels · VK · Dzen · Threads
            │
            ▼  CTA в Telegram
    ┌─────────────────────┐
    │   TELEGRAM  🔷 HUB  │
    └─────────────────────┘
            │
            ▼  /start в боте
    ┌─────────────────────┐
    │   Lead Magnet Bot   │
    └─────────────────────┘
            │
            ▼  выдача PDF / видео
    ┌─────────────────────┐
    │   Подписка на TG    │
    └─────────────────────┘
            │
            ▼  прогрев
    ┌─────────────────────┐
    │  Консультация / Курс│
    └─────────────────────┘
```

---

## ▸ Pipeline контента

```dataview
TABLE WITHOUT ID
  file.link AS "Материал",
  platform AS "Платформа",
  pillar AS "Пиллар",
  status AS "Статус"
FROM "platforms" OR "content/ideas"
WHERE status != "опубликовано"
SORT status ASC, file.mtime DESC
LIMIT 15
```

---

## ▸ Метрики недели

### Идеи в банке

```dataview
TABLE WITHOUT ID
  status AS "Статус",
  length(rows) AS "Кол-во"
FROM "content/ideas"
GROUP BY status
```

### Готово к публикации

```dataview
TABLE WITHOUT ID
  file.link AS "Материал",
  platform AS "Платформа",
  publish_date AS "Дата"
FROM "platforms" OR "content"
WHERE status = "готов"
SORT publish_date ASC
LIMIT 10
```

### Опубликовано за 7 дней

```dataview
TABLE WITHOUT ID
  file.link AS "Материал",
  platform AS "Платформа",
  pillar AS "Пиллар"
FROM "platforms" OR "content"
WHERE status = "опубликовано" AND publish_date >= date(today) - dur(7 days)
SORT publish_date DESC
```

---

## ▸ Распределение по пилларам

Цель:   💰 30%   ⚙️ 20%   📣 20%   📖 20%   🔮 10%

```dataview
TABLE WITHOUT ID
  pillar AS "Пиллар",
  length(rows) AS "Всего",
  length(filter(rows, (r) => r.status = "опубликовано")) AS "Опубл."
FROM "platforms" OR "content"
WHERE pillar != null
GROUP BY pillar
```

---

## ▸ Распределение по платформам

```dataview
TABLE WITHOUT ID
  platform AS "Платформа",
  length(rows) AS "Всего",
  length(filter(rows, (r) => r.status = "готов")) AS "Готово",
  length(filter(rows, (r) => r.status = "опубликовано")) AS "Вышло"
FROM "platforms"
WHERE platform != null
GROUP BY platform
```

---

## ▸ Календарь следующих 14 дней

```dataview
TABLE WITHOUT ID
  publish_date AS "Дата",
  platform AS "Платформа",
  pillar AS "Пиллар",
  file.link AS "Материал"
FROM "platforms" OR "content"
WHERE publish_date >= date(today) AND publish_date <= date(today) + dur(14 days)
SORT publish_date ASC
```

---

## ▸ Лид-магниты

```dataview
TABLE WITHOUT ID
  file.link AS "Магнит",
  format AS "Формат",
  target_audience AS "ЦА",
  status AS "Статус"
FROM "lead-magnets/concepts" OR "lead-magnets/published"
SORT status ASC
```

---

## ▸ Топ публикации (по метрикам)

*Заполняется `analytics` после первых 10 публикаций.*

```dataview
TABLE WITHOUT ID
  file.link AS "Материал",
  platform AS "Платформа",
  metrics.views_7d AS "Просмотры",
  metrics.tg_subs_delta_7d AS "Подписки в TG"
FROM "platforms"
WHERE status = "опубликовано" AND metrics != null
SORT metrics.views_7d DESC
LIMIT 10
```

---

## ▸ Последние инсайты analytics

Правила, которые `analytics` обновил у других агентов:

```dataview
LIST
FROM "analytics"
WHERE contains(file.name, "weekly") OR contains(file.name, "insight")
SORT file.mtime DESC
LIMIT 5
```

---

## ▸ Источники и разборы

```dataview
LIST file.link
FROM "knowledge-base/external-sources"
WHERE file.name = "README"
```

---

## ▸ Последние записи в журнале

```dataview
LIST file.mtime
FROM "JOURNAL"
SORT file.mtime DESC
LIMIT 3
```

[→ Открыть Journal](JOURNAL.md)

---

## ▸ Быстрые действия

- ➕ **Новая идея** → шаблон `_templates/idea`
- 📝 **Новый пост** → шаблон `_templates/post`
- 🎬 **Сценарий шорта** → шаблон `_templates/script`
- 📖 **Новый кейс** → шаблон `_templates/case-study`
- 💎 **Новый лид-магнит** → [lead-magnets/README.md](agents/lead-magnets/README.md)
- 🔍 **Поиск** → Cmd+P (быстрый) · Cmd+Shift+F (полный)

---

```
  ───────────────────────────────────────────────────────
   Обновления · anton@foodbusinessacademy · 2026-04-21
  ───────────────────────────────────────────────────────
```
# test
