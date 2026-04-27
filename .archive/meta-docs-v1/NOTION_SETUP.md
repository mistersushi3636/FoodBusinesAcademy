---
name: Notion Setup Guide
description: Пошаговая инструкция по организации Food Business Academy в Notion
type: guide
---

# 🔶 Notion Setup — Пошаговая инструкция

Этот гайд поможет тебе за 20 минут организовать красивое рабочее пространство в Notion.

---

## 📋 ШАГИ

### 1. Регистрация и создание Workspace

1. Зайди на https://www.notion.so
2. **Sign up** → используй Email / Google
3. Создай **Workspace** с названием: `Food Business Academy` (или своё имя)
4. Выбери шаблон: **Blank** (чистый лист)

---

### 2. Импорт всех идей из CSV (БЫСТРЫЙ СПОСОБ)

1. Скачай файл `NOTION_IMPORT.csv` из проекта
2. В Notion нажми **+ Add a page**
3. Выбери **Database → Table (inline)**
4. Назови: **Ideas**
5. Нажми на три точки (⋯) → **Import → CSV**
6. Выбери `NOTION_IMPORT.csv`
7. Готово! Все идеи загружены

**Если CSV не работает**, см. Шаг 3 (создание вручную).

---

### 3. Создание таблицы Ideas (если импорт не сработал)

1. **+ Add a page** → **Database → Table**
2. Назови: **Ideas**
3. Добавь колонки (кнопка **+** в конце таблицы):

| Колонка | Тип | Варианты |
|---|---|---|
| **Name** | Text | (автозаполняется) |
| **Pillar** | Select | 💰 Деньги \| ⚙️ Операционка \| 📣 Маркетинг \| 📖 Кейсы \| 🔮 Тренды |
| **Format** | Select | Пост \| Шортс \| Видео \| Статья \| Гайд \| Инструмент |
| **Status** | Select | Идея \| В работе \| Черновик \| Готов \| Опубликовано |
| **Platform** | Multi-select | Telegram \| YouTube \| Shorts \| Article \| Story |
| **Audience** | Multi-select | Владелец \| Повар \| Су-шеф \| Администратор \| Рекрутер |
| **Source** | Select | Grebenyuk \| Ayaz \| Собственное |
| **Publish Date** | Date | (пусто, заполняешь позже) |
| **Notes** | Text | Заметки |

4. Добавь вручную 5–10 строк идей (см. ниже примеры)

**Примеры для добавления:**
```
КПИ су-шефа | Операционка | Пост | Идея | Telegram | Су-шеф, Владелец | Grebenyuk
Запуск пачками блюд | Операционка | Пост | Идея | Telegram | Владелец, Шеф | Ayaz
Анализ конкурентов | Маркетинг | Пост | Идея | Telegram | Владелец | Ayaz
```

---

### 4. Создание Views (разные способы просмотра)

#### 4.1 Kanban View (главный поток)

1. На таблице **Ideas** нажми **+ Add a view**
2. Выбери **Kanban**
3. **Group by:** Status
4. Готово! Теперь видишь: Идеи → В работе → Черновик → Готов → Опубликовано

#### 4.2 Calendar View (график публикаций)

1. **+ Add a view** → **Calendar**
2. **Date property:** Publish Date
3. Теперь видишь когда что выпускать

#### 4.3 Gallery View (по пилларам)

1. **+ Add a view** → **Gallery**
2. **Group by:** Pillar
3. Видишь идеи сгруппированные по тематикам

#### 4.4 Filtered Table (только готовые)

1. **+ Add a view** → **Table**
2. **Filter:** Status = Готов
3. Название view: "Ready to Publish"

---

### 5. Создание главного Dashboard

1. **+ New page** (на уровне Ideas)
2. Назови: **🎯 Dashboard**
3. Добавь блоки:

**Кнопки и ссылки:**
```
Нажми /button и создай кнопки:
- 💡 Ideas (ссылка на Ideas → Kanban view)
- 📅 Calendar (ссылка на Ideas → Calendar view)
- 🎨 Gallery (ссылка на Ideas → Gallery view)
```

**Встроенные (Embed) блоки:**
```
/database
Выбери: Ideas table
Kanban view (по Status) — основной поток
```

```
/database
Выбери: Ideas table
Calendar view — видишь даты публикаций
```

**Статистика (Synced Block):**
```
/database
Выбери: Ideas table
Отфильтруй: Status = В работе
Название: "В работе (нужно доделать)"
```

---

### 6. Создание других баз (опционально)

Если нужна детализация, создай ещё таблицы:

#### **Content (готовые материалы)**
- **Name** | **Type** (TG Post / Short / Article) | **Status** | **Date published** | **Link** | **Metrics** (просмотры, лайки)

#### **External Sources (разборы)**
- **Name** (Grebenyuk / Ayaz) | **Materials Created** (связь с Ideas) | **Adaptation Date** | **Status**

#### **Publishing Calendar**
- **Date** | **Pillar** | **Platform** | **Content Link** | **Metrics** (после публикации)

---

### 7. Быстрые советы по Notion

**Быстрое добавление идеи:**
1. Нажми **Cmd+K** → Search
2. Напиши "Ideas"
3. Нажми **Create** → добавляется новая строка

**Быстрый фильтр:**
1. На любой view нажми **Filter** → добавь условие
2. Пример: `Status = В работе AND Pillar = Маркетинг`

**Шаблоны для идей:**
1. На ideas-таблице нажми **Templates** (если есть кнопка)
2. Создай template с префиллом (например, Source = Собственное)
3. Теперь каждая новая идея наследует эти значения

**Сортировка:**
1. **Sort** → выбери по какому полю (например, по дате публикации)

---

### 8. Синхронизация Obsidian + Notion

**Раз в неделю:**
1. В Obsidian смотришь DASHBOARD → что стало готово
2. В Notion обновляешь статусы в таблице Ideas
3. Notion становится витриной, Obsidian — рабочей областью

**Или используй Zapier/IFTTT:**
- (опционально) автоматическое обновление статуса из Obsidian в Notion через интеграции

---

## 🎯 ГОТОВАЯ СТРУКТУРА В NOTION

```
Food Business Academy (Workspace)
├── 🎯 Dashboard
│   ├── Кнопки (Ideas, Calendar, Gallery)
│   ├── Embedded Kanban (Ideas по Status)
│   └── Статистика (В работе, Готово)
│
├── 💡 Ideas (main table)
│   ├── Kanban view (основной поток)
│   ├── Calendar view (даты публикаций)
│   ├── Gallery view (по пилларам)
│   └── Filtered views (только готовые и т.д.)
│
├── 📝 Content (материалы)
│   ├── TG Posts
│   ├── Shorts
│   └── Articles
│
└── 📚 External Sources (разборы)
    ├── Grebenyuk
    └── Ayaz
```

---

## ⏱️ ВРЕМЯ РАБОТЫ

- **CSV импорт:** 5 мин
- **Создание views (Kanban, Calendar, Gallery):** 10 мин
- **Dashboard с embed-блоками:** 5 мин
- **Итого:** ~20 минут

---

## 🎬 ТЕСТИРОВАНИЕ

После настройки:
1. Добавь 2–3 новые идеи вручную
2. Переведи одну в статус "В работе"
3. Посмотри как она появляется в Kanban
4. Проверь Calendar (если указал дату)

**Всё работает?** Выбирай Notion как рабочее пространство и начинай!

---

## ❓ ПРОБЛЕМЫ

**CSV не импортируется?**
→ Убедись что файл в формате CSV (запятые, не точки с запятой)

**Embed блоки не появляются?**
→ Убедись что у тебя **Notion Pro** (или используй простую ссылку на database)

**Calendar не показывает даты?**
→ Убедись что:
  - Колонка **Publish Date** создана и имеет тип Date
  - В строках заполнены даты (не пусто)
