---
type: documentation
updated: 2026-04-24
---

# ideas-bot/

Идеи Антона — от первой мысли до реализации. Каждая идея — отдельный markdown-файл, движется по статусам.

## Статусы (канбан-пайплайн)

```
incoming → analyzing → refined → planned → in-progress → completed → archived
```

| Папка | Статус | Кто заполняет |
|---|---|---|
| `incoming/` | Новая, необработанная | Telegram-бот (голос/текст) |
| `analyzing/` | На анализе у idea-curator | Агент idea-curator |
| `refined/` | Антон уточнил, ждёт плана | Антон через бот |
| `planned/` | Есть план реализации | Агент idea-curator |
| `in-progress/` | Идея в работе | Антон через бот |
| `completed/` | Завершена и опубликована | Антон через бот |
| `archived/` | Отложена / не актуальна | Антон через бот |

## Формат файла идеи

```markdown
---
title: Краткое название идеи
type: content | product | operations | marketing | tech | other
pillar: money | operations | marketing | cases | trends | null
source: telegram-text | telegram-voice | manual
status: incoming
created: YYYY-MM-DDTHH:MM:SS
analyzed_at: YYYY-MM-DDTHH:MM:SS  # заполняет idea-curator
score:
  potential: 8
  uniqueness: 7
  feasibility: 9
  urgency: 6
  total: 7.5
---

[Текст идеи как написал/сказал Антон]

## Анализ (idea-curator)

[Заполняет агент]

## История диалогов

[Уточнения от Антона через бот]

## План реализации

[Заполняет idea-curator по запросу]
```

## Как попадают идеи

### Через Telegram-бот
1. Антон нажимает «💡 Новая идея» → пишет текст → бот сохраняет в `incoming/`
2. Или нажимает «🎙️ Голос → пост» → Whisper расшифровывает → выбирает «Как идея»
3. Или отправляет голосовое в любой момент → автоматически попадает в `incoming/`

### Вручную
Создать файл в `incoming/` с frontmatter выше.

### Через Claude Code
```bash
claude -p /idea-curator "текст идеи"
```

## Агент idea-curator

Обрабатывает идеи автоматически. Запускается:
- Сразу при получении идеи через бот
- Вручную: `/idea-curator` с путём к файлу

Что делает:
1. Классифицирует по типу и пиллару FBA
2. Оценивает (потенциал, уникальность, реализуемость, срочность)
3. Находит сильные и слабые места
4. Проверяет дубли
5. Задаёт 2-3 уточняющих вопроса если нужно
6. Предлагает 3 варианта реализации (минимум/стандарт/максимум)
7. Перемещает в `analyzing/` и уведомляет Антона через бот

## Связанные файлы

- Агент: `agents/functional/idea-curator.md`
- Скилл: `~/.claude/skills/idea-curator/SKILL.md`
- Бот хендлер: `bots/anton-assistant/handlers/ideas.py`
- Vault writer: `bots/anton-assistant/services/vault_writer.py`
