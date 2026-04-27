---
name: FBA Sync System
description: Архитектура синхронизации данных между Obsidian, Claude, Google Sheets и Dashboard
type: reference
category: architecture
---

# 🔄 FBA SYNC SYSTEM — Полная Архитектура

**Статус:** 🟢 АКТИВНА | **Обновлено:** 2026-04-24 | **Version:** 1.0

---

## 📊 Обзор Системы

```
┌─────────────────────────────────────────────────────────────┐
│                    SOURCES OF TRUTH                         │
├─────────────────────────────────────────────────────────────┤
│  📄 Markdown Files (Obsidian)    ← Primary source          │
│  📑 CSV File (Google Sheets)     ← Secondary source        │
│  🤖 Claude API                   ← Processing layer        │
│  📊 Dashboard (HTML/JS)          ← Visualization layer     │
└─────────────────────────────────────────────────────────────┘
         ↓              ↓               ↓              ↓
    Read/Write      Import/          Tools          LocalStore
    via Edit        Export            API            + Display
```

---

## 🎯 Точки Синхронизации

### 1️⃣ OBSIDIAN VAULT ↔ CLAUDE API

**Направление:** Двусторонняя (bidirectional)

| Операция | Как | Когда | Формат |
|----------|-----|-------|--------|
| **Чтение** | `Read` tool | На каждый запрос | Markdown + YAML |
| **Запись** | `Write` tool | После обновления | Markdown |
| **Обновление** | `Edit` tool | Изменение задачи | Diff-based |

**Файлы для синхро:**
```
LAUNCH-CHECKLIST.md          (86 задач)
platforms/*/calendar.md      (8 платформ)
agents/README.md             (18 агентов)
WORKSPACE.md                 (рабочее пространство)
```

**Пример синхро:**
```markdown
---
sync: true                   # Флаг синхронизации
last_updated: 2026-04-24    # Последнее обновление
source: FBA-Launch-Checklist.csv
---

- [ ] #1 Выбрать никнейм | Антон | P0 | Неделя 1
      ↓ Claude читает checkboxes
      ↓ Обновляет статус when task completed
- [x] #2 Проверить доступность | Антон | P0 | Неделя 1
```

---

### 2️⃣ GOOGLE SHEETS ↔ OBSIDIAN

**Направление:** Двусторонняя

| Операция | Как | Когда | Данные |
|----------|-----|-------|--------|
| **Import** | CSV → MD | На старте проекта | Column headers → YAML |
| **Export** | MD → CSV | На сохранение листа | Checkboxes → TRUE/FALSE |
| **Sync status** | Sheet cell | Real-time | ✅ / ⏳ / ❌ |

**Google Sheets структура:**
```
Col A: ✅ (FALSE → checkbox)
Col B: № (task ID)
Col C: Раздел (section)
Col D: Задача (task name)
Col E: Агент (assigned agent)
Col F: Приоритет (P0/P1/P2)
Col G: Срок (week)
Col H: Статус (not started / in progress / done)
Col I: Ссылки/Заметки (links & notes)
```

**Импорт в Google Sheets:**
1. Скопировать CSV в новый Google Sheet
2. Column A: Insert → Checkbox
3. Format → checkboxes (FALSE → unchecked, TRUE → checked)

---

### 3️⃣ DASHBOARD ↔ LIVE DATA

**Направление:** Одностороння (read from Obsidian) + Real-time display

| Компонент | Источник | Обновление | Сохранение |
|-----------|----------|-----------|-----------|
| Метрики (86 tasks) | LAUNCH-CHECKLIST.md | Auto-parse | LocalStorage |
| Статус по агентам | Parse checkboxes | On checkbox change | In-memory |
| Платформы (8) | platforms/*/calendar.md | Auto-parse | In-memory |
| Визуализация | HTML/JS | Real-time | Browser cache |

**Dashboard интеграция:**
```javascript
// Dashboard читает данные
const tasks = parseCsv('FBA-Launch-Checklist.csv');
const platforms = parseYaml('platforms/*/calendar.md');

// Отображает live
updateMetrics({
  total: 86,
  completed: getCompletedCount(),
  inProgress: getInProgressCount(),
  pending: getPendingCount()
});

// Сохраняет в localStorage
localStorage.setItem('fba-state', JSON.stringify(state));
```

---

### 4️⃣ CLAUDE API ↔ ALL

**Направление:** Центральный hub

```
Claude API
  ├─ Reads from: Obsidian (MD), Google Sheets (CSV)
  ├─ Writes to: Obsidian (MD), Google Sheets (API)
  ├─ Updates: Dashboard (via data files)
  └─ Processes: All automation & transformations
```

**Claude workflow:**
```
User command
  ↓
Claude reads files (Obsidian, CSV)
  ↓
Process & update (add tasks, change status, etc.)
  ↓
Write back (to Obsidian markdown)
  ↓
Update Google Sheets (via CSV export)
  ↓
Dashboard auto-refreshes (detects file changes)
```

---

## 📡 Протокол Синхронизации

### Цикл синхронизации (Sync Cycle)

**Периодичность:** Real-time (на требование) + Auto-refresh (5 мин)

```timeline
T0: User opens dashboard
  └─ Reads LAUNCH-CHECKLIST.md (fresh data)
  └─ Parses CSV from Google Sheets
  └─ Renders UI

T1-T4: User makes changes
  └─ Checkbox toggled in dashboard
  └─ State saved to localStorage
  
T5: Claude reads state
  └─ Updates LAUNCH-CHECKLIST.md
  └─ Marks task as completed
  └─ Updates Google Sheets
  
T10: Dashboard auto-refreshes (5 min interval)
  └─ Re-reads LAUNCH-CHECKLIST.md
  └─ Updates all metrics
  └─ Reflects new status
```

### Обработка конфликтов (Conflict Resolution)

| Конфликт | Решение | Приоритет |
|----------|---------|-----------|
| Obsidian ≠ CSV | Obsidian wins (source of truth) | Markdown > CSV |
| Dashboard ≠ Obsidian | Re-read & refresh | Obsidian > Dashboard |
| Claude ≠ Dashboard | Claude updates all sources | API writes final |

**Правило:** Obsidian markdown файлы — единственный источник правды (SSOT)

---

## 🔧 Техническая Реализация

### Файлы, участвующие в синхро

```
/Users/anton/Food Business Academy/
├── LAUNCH-CHECKLIST.md               ← Master checklist (sync: true)
├── FBA-Launch-Checklist.csv          ← CSV export (import source)
├── WORKSPACE-DASHBOARD-RU.html       ← Dashboard (live metrics)
├── .obsidian/
│   └── plugins/obsidian-dashboard/
│       └── dashboards/fba-main.yaml  ← Dashboard config
├── platforms/
│   ├── telegram/calendar.md          ← TG schedule (dataview query)
│   ├── youtube/calendar.md
│   ├── tiktok/calendar.md
│   ├── instagram/calendar.md
│   ├── vk/calendar.md
│   ├── dzen/calendar.md
│   ├── max/calendar.md
│   └── threads/calendar.md
└── agents/README.md                  ← Agent assignments (dataview)
```

### Формат YAML Frontmatter

```yaml
---
name: FBA Launch Checklist
description: Полный чеклист запуска
type: checklist
status: active
sync: true                    # ← Включить синхронизацию
source: FBA-Launch-Checklist.csv
last_updated: 2026-04-24     # Auto-update на каждую синхро
sync_to: ["google-sheets", "dashboard", "claude"]
---
```

### DataView Queries (Obsidian)

```dataview
TABLE
  WITHOUT ID
  file.name as "Раздел",
  rows as "Задач"
FROM ""
WHERE type = "checklist" AND sync = true
GROUP BY file.folder
SORT file.folder ASC
```

---

## 📤 Процесс Синхронизации

### ✅ Когда задача завершена

**Шаг 1:** User checks checkbox в dashboard/Obsidian
```markdown
- [x] #1 Выбрать никнейм | Антон | P0 | Неделя 1
```

**Шаг 2:** Claude обнаруживает изменение
```javascript
// Read LAUNCH-CHECKLIST.md
const tasks = readMarkdownCheckboxes(file);
const completed = tasks.filter(t => t.checked === true);
```

**Шаг 3:** Update statistics
```
Total: 86
Completed: 1
In Progress: 0
Pending: 85
Completion: 1.16%
```

**Шаг 4:** Sync to all sources
```
Obsidian: ✅ Update last_updated timestamp
Google Sheets: ✅ Update row status to "Завершено"
Dashboard: ✅ Auto-refresh metrics
Claude: ✅ Log completion
```

### 📝 Когда добавляется новая задача

**Шаг 1:** Claude creates task in LAUNCH-CHECKLIST.md
```markdown
- [ ] #87 New task | Agent | P0 | Week 5
```

**Шаг 2:** YAML frontmatter updates automatically
```yaml
last_updated: 2026-04-24T15:30:00Z
```

**Шаг 3:** Google Sheets syncs (via CSV export)
```
New row added to FBA-Launch-Checklist
FALSE | 87 | Раздел | Новая задача | ...
```

**Шаг 4:** Dashboard reflects change
```
Total tasks: 87 (was 86)
Metrics refresh automatically
```

---

## 🎯 Примеры Синхронизации

### Пример 1: Завершить задачу в Obsidian

```
1. Open LAUNCH-CHECKLIST.md
2. Check checkbox: - [ ] → - [x]
3. Save file (Ctrl+S)
4. Dashboard detects change (5 min auto-refresh OR manual refresh)
5. Metrics update: Completed +1
6. Google Sheets auto-updates (CSV)
7. Claude logs completion
```

### Пример 2: Добавить новый пост в TG

```
1. Claude creates new task in LAUNCH-CHECKLIST.md
2. Adds to section 2 (TELEGRAM)
3. Assigns to telegram-agent
4. Sets priority P0, week 1
5. Dashboard parses & shows new task
6. Google Sheets imports new row
7. Agent notification (via Claude message)
```

### Пример 3: Update платформы расписание

```
1. Edit platforms/telegram/calendar.md
2. Update publish_date in frontmatter
3. Modify rhythm (e.g., Пн 08:30 → Пн 09:00)
4. Save file
5. Dashboard calendar updates
6. Obsidian dashboard plugin refreshes
7. All linked views update automatically
```

---

## 🚀 Включение Синхронизации

### На стороне Obsidian

✅ **Требует:**
- Obsidian Desktop или Web Clipper
- Obsidian Dashboard plugin (нужно установить)
- Dataview plugin (обычно встроен)

✅ **Не требует:**
- Cloud sync (работает локально)
- Plugins configuration (auto-detect via YAML)

### На стороне Claude

✅ **Требует:**
- Доступ к файлам (Read/Write tools)
- CSV парсинг (встроено)
- Markdown парсинг (встроено)

✅ **Не требует:**
- Дополнительные API
- Установка пакетов

### На стороне Google Sheets

✅ **Требует:**
- Создать новый Google Sheet
- Импортировать FBA-Launch-Checklist.csv
- Скопировать заголовки в первую строку

✅ **Не требует:**
- Google Sheets API
- Advanced permissions

---

## 📊 Статус Системы

| Компонент | Статус | Примечание |
|-----------|--------|-----------|
| Obsidian Markdown | 🟢 Active | LAUNCH-CHECKLIST.md created |
| CSV Source | 🟢 Active | FBA-Launch-Checklist.csv ready |
| Dashboard (RU) | 🟢 Ready | WORKSPACE-DASHBOARD-RU.html |
| Claude API | 🟢 Ready | Read/Write tools available |
| Google Sheets | 🟡 Manual | Requires CSV import once |
| Obsidian Dashboard | 🟡 Config ready | fba-main.yaml created, needs plugin |

---

## 🔗 Быстрые Ссылки

- [[LAUNCH-CHECKLIST|Master Checklist]]
- [[FBA-Launch-Checklist.csv|CSV Source]]
- [[WORKSPACE-DASHBOARD-RU|Russian Dashboard]]
- [[agents/README|Agent Architecture]]
- [[OBSIDIAN_SETUP|Obsidian Setup]]

---

**Last sync:** 2026-04-24 15:32 UTC
**Sync interval:** Real-time (on demand) + 5 min auto-refresh
**Source of truth:** `/Users/anton/Food Business Academy/LAUNCH-CHECKLIST.md`