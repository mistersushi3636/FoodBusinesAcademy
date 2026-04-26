---
name: Instagram Calendar
description: Редакционный план Instagram
type: calendar
platform: instagram
---

# 📸 Instagram — редплан

**Ритм:** 3 Reels/нед + Stories по ситуации
**Время:** 12:00 и 20:00 (МСК)
**CTA:** ссылка в bio → TG-канал

| Формат | Частота |
|---|---|
| Reels | 3/нед |
| Карусель | 1/нед (по желанию) |
| Stories | ситуативно |

---

## Очередь

```dataview
TABLE pillar AS "Пиллар", publish_date AS "Дата", status AS "Статус"
FROM "platforms/instagram"
WHERE status != "опубликовано"
SORT publish_date ASC
```
