---
name: YouTube Calendar
description: Редакционный план YouTube-канала
type: calendar
platform: youtube
---

# 📺 YouTube — редплан

**Ритм:** 1 длинное видео/нед · 2 Shorts/нед
**Время публикации:** Вт 12:00 (длинное) · Чт+Сб 10:00 (Shorts)

| Формат | Частота | Длина |
|---|---|---|
| Длинное видео | 1/нед | 7–20 мин |
| YouTube Shorts | 2/нед | 30–60 сек |

---

## Очередь

```dataview
TABLE pillar AS "Пиллар", publish_date AS "Дата", status AS "Статус"
FROM "platforms/youtube"
WHERE type = "script" AND status != "опубликовано"
SORT publish_date ASC
```

## Опубликовано

```dataview
TABLE pillar AS "Пиллар", publish_date AS "Дата"
FROM "platforms/youtube"
WHERE status = "опубликовано"
SORT publish_date DESC
LIMIT 10
```
