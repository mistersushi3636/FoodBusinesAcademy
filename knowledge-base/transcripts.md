---
name: Расшифровки голосовых
description: Транскрипты голосовых заметок Антона — сырьё для контента
type: index
---

# 🎙️ Расшифровки голосовых

> Сырьё. Антон записывает голосовое → content-assistant бот транскрибирует → файл сюда.
> Из каждой расшифровки получается: пост TG + 3 идеи шортсов + тезисы YouTube.

```dataview
TABLE file.size AS "Размер", file.mtime AS "Дата"
FROM "knowledge-base/transcripts"
SORT file.mtime DESC
```
