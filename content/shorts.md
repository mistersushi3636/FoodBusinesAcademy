---
name: Сценарии шортсов
description: Сценарии коротких видео — TikTok / Reels / YouTube Shorts
type: index
---

# ⚡ Сценарии шортсов

> Короткие вертикальные видео 15–60 сек. TikTok / Reels / YouTube Shorts.

```dataview
TABLE pillar AS "Пиллар", status AS "Статус", platform AS "Площадка"
FROM "content/shorts"
WHERE type = "script"
SORT file.mtime DESC
```

---

Создать сценарий шортса: `Cmd+N` → имя → `Cmd+P` → Insert template → `script`
