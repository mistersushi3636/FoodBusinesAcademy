---
name: Длинные тексты
description: Статьи для Дзен, VC, лонгриды
type: index
---

# 📝 Длинные тексты

> Статьи для Дзен / VC.ru / лонгриды (1500–5000 зн.). SEO-хвост → ведут в TG.

```dataview
TABLE pillar AS "Пиллар", status AS "Статус", platform AS "Площадка"
FROM "content/articles"
WHERE type = "post"
SORT file.mtime DESC
```

---

Создать статью: `Cmd+N` → имя → `Cmd+P` → Insert template → `post`
