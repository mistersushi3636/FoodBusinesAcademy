---
name: Telegram Calendar
description: Редакционный план Telegram-канала
type: calendar
platform: telegram
---

# 🔷 Telegram — редплан

**Ритм:** Пн 08:30 · Ср 13:00 · Пт 19:30 (МСК)

| Пиллар | День | Тип |
|---|---|---|
| 💰 Деньги | Понедельник | Разбор цифр / P&L |
| ⚙️ Кейсы / Операционка | Среда | Личный опыт |
| 📣 Маркетинг / Тренды | Пятница | Лайфхак / инструмент |

---

## Очередь публикаций

```dataview
TABLE pillar AS "Пиллар", publish_date AS "Дата", status AS "Статус"
FROM "platforms/telegram/posts"
WHERE status != "опубликовано"
SORT publish_date ASC
```

## Опубликовано

```dataview
TABLE pillar AS "Пиллар", publish_date AS "Дата"
FROM "platforms/telegram/posts"
WHERE status = "опубликовано"
SORT publish_date DESC
LIMIT 10
```
