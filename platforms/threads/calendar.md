---
name: Threads Calendar
description: Редакционный план Threads
type: calendar
platform: threads
---

# 🧵 Threads — редплан

**Ритм:** 3–5 коротких текстов/нед
**Формат:** короткие мысли 150–300 зн. (вытяжки из постов TG)
**Цель:** точечное касание → TG-канал

---

## Очередь

```dataview
TABLE publish_date AS "Дата", status AS "Статус"
FROM "platforms/threads"
WHERE status != "опубликовано"
SORT publish_date ASC
```
