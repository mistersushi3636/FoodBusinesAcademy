---
name: Сценарии видео
description: Сценарии длинных YouTube-видео
type: index
---

# 🎬 Сценарии видео

> Длинные видео YouTube (5–30 мин). Один файл = один сценарий.

```dataview
TABLE pillar AS "Пиллар", status AS "Статус", publish_date AS "Дата"
FROM "content/scripts"
WHERE type = "script"
SORT file.mtime DESC
```

---

Создать новый сценарий: `Cmd+N` → имя → `Cmd+P` → Insert template → `script`
