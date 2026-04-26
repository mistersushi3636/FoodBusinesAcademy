---
name: FAQ аудитории
description: Вопросы из комментариев, DM, эфиров — готовые темы для контента
type: index
---

# ❓ FAQ аудитории

> Вопросы из комментариев, DM, Telegram, эфиров. Каждый вопрос — потенциальный пост или шортс.

```dataview
TABLE status AS "Статус", platform AS "Источник", file.mtime AS "Добавлен"
FROM "knowledge-base/faq"
SORT file.mtime DESC
```

---

Добавить вопрос: `Cmd+N` → имя → `Cmd+P` → Insert template → `audience-question`
