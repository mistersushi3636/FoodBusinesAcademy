---
name: VK Calendar
description: Редакционный план ВКонтакте
type: calendar
platform: vk
---

# 🔵 ВКонтакте — редплан

**Ритм:** 2 поста/нед (Вт + Пт)
**Время:** 12:00 (МСК) — аудитория 30+, дневная активность
**Формат:** адаптация постов TG + Клипы (= шортсы)
**CTA:** каждый пост → ссылка на TG-канал

---

## Очередь

```dataview
TABLE pillar AS "Пиллар", publish_date AS "Дата", status AS "Статус"
FROM "platforms/vk"
WHERE status != "опубликовано"
SORT publish_date ASC
```
