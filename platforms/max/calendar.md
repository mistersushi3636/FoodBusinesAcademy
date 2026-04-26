---
name: MAX Calendar
description: Редакционный план MAX (VK Мессенджер)
type: calendar
platform: max
---

# 💬 MAX — редплан

**Ритм:** зеркало TG (авторепост или ручной)
**Формат:** те же посты что в TG — без изменений
**Цель:** охват аудитории VK-экосистемы

---

## Очередь

```dataview
TABLE publish_date AS "Дата", status AS "Статус"
FROM "platforms/max"
WHERE status != "опубликовано"
SORT publish_date ASC
```
