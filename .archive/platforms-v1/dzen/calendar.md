---
name: Дзен Calendar
description: Редакционный план Яндекс Дзен
type: calendar
platform: dzen
---

# 📰 Дзен — редплан

**Ритм:** 2 статьи/нед
**Формат:** лонгриды 1500–4000 зн. (адаптация постов TG в SEO-статьи)
**Цель:** органический SEO-трафик → TG-канал
**Ключевые слова:** доставка еды / ресторанный бизнес / открыть доставку / общепит

---

## Очередь

```dataview
TABLE pillar AS "Пиллар", publish_date AS "Дата", status AS "Статус"
FROM "platforms/dzen"
WHERE status != "опубликовано"
SORT publish_date ASC
```
