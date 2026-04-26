---
name: Map of Content
description: Главный дашборд проекта Food Business Academy
type: hub
---

# 🗺️ Food Business Academy — MOC

> Главная карта проекта. Отсюда навигация по всему vault.

👉 **ГЛАВНЫЙ ДАШБОРД:** [[DASHBOARD]] (процессы, агенты, метрики)
🤖 **КОМАНДА АГЕНТОВ:** [[agents/README|agents/]] (orchestrator + functional + platform + lead-magnets)
🎨 **ДИЗАЙН-СИСТЕМА:** [[design-system/README|design-system]] (брендбук, AI-промпты)
💎 **ЛИД-МАГНИТЫ:** [[agents/lead-magnets/README|lead-magnets]] (3 агента воронки)
📦 **КОНТЕНТ-БАНК:** [[content-bank/README|content-bank]] (по форматам)
📱 **ПЛАТФОРМЫ:** [[platforms/README|platforms]] (готовые материалы по каждой соцсети)
📔 **ПАМЯТЬ ПРОЕКТА:** [[JOURNAL]] (решения и инсайты)
📊 **РАБОЧЕЕ ПРОСТРАНСТВО:** [[WORKSPACE]] (Obsidian — основное)

---

📌 **Проект:** Экспертный личный бренд Антона Коваленко.
🎯 **Фаза:** Запуск (90 дней).
🎨 **Контекст:** Food Business Academy для рестораторов и предпринимателей в общепите.

---

## 🚀 Быстрые действия

- 📝 Новая идея → создай из шаблона `_templates/idea`
- 📮 Новый пост → `_templates/post`
- 🎬 Сценарий шортса/видео → `_templates/script`
- 📖 Новый кейс → `_templates/case-study`
- ❓ Ответ на вопрос аудитории → `_templates/audience-question`
- 🗂️ Канбан контента → [[content/kanban|Канбан]]
- 📓 Записать решение/инсайт → [[JOURNAL]]

---

## 🎨 Бренд

- [[brand/positioning|Позиционирование]] — кто я, для кого, чем отличаюсь
- [[brand/audience|Аудитория]] — 3 портрета ЦА
- [[brand/tone-of-voice|Tone of Voice]] — как говорю

---

## 📝 Контент

- [[content/pillars|5 контент-пилларов]]
- [[content/calendar|Редакционный календарь]]
- [[content/kanban|Канбан — конвейер постов]]
- Папки:
  - [[content/ideas|Идеи]] — 1 идея = 1 файл
  - [[content/scripts|Сценарии видео]]
  - [[content/shorts|Сценарии шортсов]]
  - [[content/articles|Длинные тексты]]

### Пиллары (теги)
- `#пилар/деньги` 💰 — 30%
- `#пилар/операционка` ⚙️ — 20%
- `#пилар/маркетинг` 📣 — 20%
- `#пилар/кейсы` 📖 — 20%
- `#пилар/тренды` 🔮 — 10%

---

## 🎯 Площадки

- [[platforms/telegram-strategy|Telegram — главный хаб]]
- [[platforms/youtube-strategy|YouTube — длинные]]
- [[platforms/shorts-strategy|Shorts/Reels/TikTok]]

---

## 🤖 Боты

- [[bots/README|Архитектура 4 ботов]]
- [[bots/lead-magnet-bot/README|Lead-magnet-bot]]
- [[bots/content-assistant/README|Content-assistant]]
- [[bots/ai-consultant/README|AI-consultant]]
- [[bots/sales-bot/README|Sales-bot]]

---

## 📚 База знаний

- [[knowledge-base/transcripts|Расшифровки голосовых]]
- [[knowledge-base/case-studies|Кейсы «Мистер Суши»]]
- [[knowledge-base/faq|FAQ аудитории]]

---

## 💼 Продукты

- [[products/courses|Бэклог курсов]]
- [[products/consultations|Консультации]]
- [[products/lead-magnets|Лид-магниты]]

---

## 📊 Аналитика

- [[analytics/metrics|Метрики]]

---

## 🗓️ Роадмап 90 дней

| Период | Фокус | Статус |
|---|---|---|
| Неделя 1–2 | Бренд-документы, 10 идей, 5 скиллов, MVP content-assistant | 🟡 |
| Неделя 3–4 | Первый чек-лист, lead-magnet-bot, 3 поста TG, пилотный YouTube | ⚪ |
| Месяц 2 | Ритм 3 поста/нед TG + 1 видео/нед + 2 шортса/нед | ⚪ |
| Месяц 3 | Пилотные консультации, прототип ai-consultant | ⚪ |

Статусы: 🟢 готово · 🟡 в работе · ⚪ не начато · 🔴 заблокировано

---

## ⚡ Claude-скиллы

- `/voice-to-post` — голосовое → пост Telegram
- `/content-idea` — генератор идей по 5 пилларам
- `/script-writer` — сценарии видео/шортсов
- `/repurpose` — длинное видео → 5–7 единиц контента
- `/audience-question` — ответы на вопросы аудитории

---

## 📈 Dataview-запросы (включи плагин Dataview)

### Идеи в работе
```dataview
TABLE pillar AS "Пиллар", status AS "Статус", platform AS "Площадка"
FROM "content/ideas"
WHERE status != "опубликовано"
SORT file.mtime DESC
```

### Черновики постов
```dataview
TABLE pillar AS "Пиллар", publish_date AS "Дата"
FROM "content"
WHERE type = "post" AND status = "черновик"
SORT publish_date ASC
```

### Опубликовано за последние 30 дней
```dataview
TABLE pillar AS "Пиллар", platform AS "Площадка", publish_date AS "Дата"
FROM "content"
WHERE status = "опубликовано" AND publish_date >= date(today) - dur(30 days)
SORT publish_date DESC
```
