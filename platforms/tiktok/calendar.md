---
name: TikTok Calendar
description: Редакционный план TikTok
type: calendar
platform: tiktok
---

# 🎵 TikTok — редплан

**Ритм:** 2–3 видео/нед
**Время:** 18:00–21:00 (МСК) — пиковая активность
**CTA:** каждый ролик → ссылка в bio → TG-канал

---

## Очередь

```dataview
TABLE pillar AS "Пиллар", publish_date AS "Дата", status AS "Статус"
FROM "platforms/tiktok"
WHERE status != "опубликовано"
SORT publish_date ASC
```
