---
name: Brand Examples
description: Реальные посты Антона — эталоны тона для LLM. Без них голос будет «средний».
type: reference
---

# 📚 Brand Examples — эталоны тона

LLM использует tone-of-voice.md как теорию, **этот каталог как практику**.

## Как заполнить

Положить сюда 5-10 реальных постов Антона из его TG/IG/YT (любых, но желательно разные пиллары):

```
examples/
  tg-2025-12-15-naym-povara.md
  tg-2026-01-08-marzha.md
  ig-2026-02-12-reels-burger.md
  yt-2025-11-03-otkrytie-filiala-script.md
  ...
```

## Формат файла-примера

```markdown
---
platform: tg | ig | yt
date: YYYY-MM-DD
pillar: 💰 | ⚙️ | 📣 | 📖 | 🔮
metric_views: 1240
metric_reactions: 89
why_it_worked: [короткая заметка от Антона]
---

[ТЕКСТ ПОСТА КАК ОН БЫЛ ОПУБЛИКОВАН]
```

`/draft` skill читает все файлы в этой папке для калибровки голоса.

⚠️ **Эта папка пустая на момент создания FBA 2.0.** Заполни до первого боевого поста — иначе LLM будет генерить усреднённый стиль.
