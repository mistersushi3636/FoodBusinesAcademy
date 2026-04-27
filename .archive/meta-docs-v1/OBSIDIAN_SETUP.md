# 🔧 Настройка Obsidian для Food Business Academy

Разовая настройка на ~15 минут. Потом vault просто работает.

---

## 1. Установка

1. Скачай Obsidian: https://obsidian.md/download
2. Открой Obsidian → **«Open folder as vault»** → выбери папку `/Users/anton/Food Business Academy`
3. Если спросит «Trust author and enable plugins?» — **Trust**

Всё, vault открыт. Начни с файла [[MOC]] — это главный дашборд.

---

## 2. Включи нужные плагины

### Core plugins (встроенные, просто включить)
Settings → Core plugins:

- ✅ **Templates** — вставка шаблонов
- ✅ **Daily notes** — ежедневные заметки
- ✅ **Tags pane** — список тегов сбоку
- ✅ **Outline** — оглавление текущей ноты
- ✅ **Graph view** — визуальный граф связей
- ✅ **Backlinks** — обратные ссылки
- ✅ **Outgoing links** — исходящие ссылки
- ✅ **Quick switcher** — Cmd+O для быстрого перехода
- ✅ **Command palette** — Cmd+P

### Community plugins (поставить)
Settings → Community plugins → **Turn on community plugins** → Browse:

1. **Kanban** (by mgmeyers) — для [[content/kanban]]
2. **Dataview** (by blacksmithgu) — для живых списков идей/постов в [[MOC]]
3. **Tasks** (by Clare Macrae) — умные чек-листы с дедлайнами _(опционально)_
4. **Calendar** (by liamcain) — мини-календарь в сайдбаре для daily notes _(опционально)_

---

## 3. Настрой Templates

Settings → Templates:
- **Template folder location:** `_templates`

Теперь в любой ноте `Cmd+P` → **Insert template** вставляет шаблон.

Быстрый способ создать пост: `Cmd+N` → дай имя → `Cmd+P` → Insert template → `post`.

---

## 4. Настрой Daily notes

Settings → Daily notes:
- **New file location:** `knowledge-base/daily`
- **Template file location:** `_templates/daily-note`
- **Date format:** `YYYY-MM-DD`

Теперь каждый день одним кликом появляется запись с целями/инсайтами.

---

## 5. Настрой Kanban

Открой [[content/kanban]]. Obsidian увидит `kanban-plugin: board` в frontmatter и покажет как доску.
Перетаскивай карточки мышью: **Идеи → В работе → Редактура → Готово → Опубликовано**.

---

## 6. Hotkeys (рекомендую)

Settings → Hotkeys:
- **Open MOC:** `Cmd+H` (Quick switcher → MOC)
- **Open JOURNAL:** отдельный хоткей
- **Insert template:** `Cmd+T`
- **Toggle left sidebar:** `Cmd+\`

---

## 7. Структура vault (уже готова)

```
Food Business Academy/
├── MOC.md                ← ГЛАВНЫЙ ДАШБОРД, начинай отсюда
├── JOURNAL.md            ← решения и контекст (память между сессиями)
├── OBSIDIAN_SETUP.md     ← этот файл
├── README.md             ← публичное описание проекта
│
├── _templates/           ← шаблоны (Templates plugin)
│   ├── post.md
│   ├── idea.md
│   ├── case-study.md
│   ├── audience-question.md
│   ├── script.md
│   └── daily-note.md
│
├── brand/                ← позиционирование, ЦА, tone of voice
├── content/
│   ├── kanban.md         ← канбан-доска контента
│   ├── pillars.md
│   ├── calendar.md
│   ├── ideas/            ← 1 идея = 1 файл (из шаблона idea)
│   ├── scripts/          ← сценарии длинных видео
│   ├── shorts/           ← сценарии шортсов
│   └── articles/
│
├── platforms/            ← стратегии Telegram / YouTube / Shorts
├── bots/                 ← 4 бота
├── knowledge-base/
│   ├── transcripts/      ← расшифровки голосовых
│   ├── case-studies/     ← кейсы Мистер Суши
│   ├── faq/              ← вопросы аудитории
│   └── daily/            ← daily notes (создаст плагин)
├── products/
└── analytics/
```

---

## 8. Frontmatter — единая схема

Каждая «рабочая» заметка (идея/пост/кейс/сценарий) начинается с YAML-frontmatter:

```yaml
---
type: idea        # idea | post | script | case-study | audience-question | daily
status: backlog   # backlog | черновик | редактура | готов | опубликовано
pillar: деньги    # деньги | операционка | маркетинг | кейсы | тренды
platform: telegram  # telegram | youtube | shorts | article
publish_date: 2026-05-01
tags:
  - идея
---
```

Dataview на [[MOC]] использует эти поля для живых списков. **Меняй статус — обновляется дашборд.**

---

## 9. Синхронизация между устройствами (опционально)

3 варианта:
1. **iCloud** — папка `/Users/anton/Food Business Academy` уже в Mac. Перенеси в `iCloud Drive` — появится на iPhone/iPad в приложении Obsidian.
2. **Obsidian Sync** — $10/мес, официальный, шифрованный.
3. **GitHub** — `git init` и коммиты. Бонус: полная история изменений.

Рекомендую сейчас: ничего не включать, работать локально. Через 2 недели, когда будет понятно, что нужен телефон — выбрать iCloud или Sync.

---

## 10. Совместная работа с Claude

Claude (я) работает напрямую с этими .md-файлами. Когда вернёшься в следующую сессию:

1. Я читаю [[JOURNAL]] — вспоминаю контекст и решения.
2. Я читаю [[MOC]] — вижу статус направлений.
3. Работаем дальше.

Если хочешь что-то зафиксировать на будущее — просто скажи «запиши в JOURNAL: …» или «запомни: …».

---

## Проверка, что всё работает

- [ ] Vault открылся, видно [[MOC]] как стартовую страницу
- [ ] Включены плагины Templates, Daily notes, Kanban, Dataview
- [ ] [[content/kanban]] открывается как канбан-доска
- [ ] На [[MOC]] внизу работают Dataview-запросы (покажут пустые таблицы — норм, пока нет данных)
- [ ] `Cmd+P` → Insert template → `post` вставляет шаблон поста
