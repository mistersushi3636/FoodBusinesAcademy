---
name: Content Bank
description: Банк контента сгруппированный по формату — источник для платформенных адаптаций
type: hub
---

# 📦 Content Bank — банк по форматам

> Сырьё, сгруппированное **по формату**, а не по платформе. Одно ядро → много платформенных версий.

Это реализация «Варианта C» из обсуждения архитектуры: группировка по формату даёт экономию — один сценарий короткого видео может пойти в TikTok, Reels, Shorts, VK Clips и Dzen.

---

## Структура

```
content-bank/
├── short-video/    ← источник для TikTok, Reels, YT Shorts, VK Clips, Dzen Video
├── long-video/     ← источник для YouTube, VK Long, Dzen Video
├── text/           ← источник для Telegram, VK Posts, Threads, Max, Dzen Articles
└── visual/         ← источник для Instagram (посты, карусели) + визуалы для всех
```

---

## Как работает

1. **Antoн создаёт сырьё** (голосовое, идея, кейс)
2. **content-adapter** или **orchestrator** кладёт ядро в соответствующую папку content-bank
3. **platform-агенты** берут ядро и делают свою адаптированную версию в `platforms/<name>/`
4. Финальная публикация хранится в `platforms/`, метаданные метрик собирает `analytics`

---

## Формат файла в banks

Каждый файл — markdown с frontmatter:

```yaml
---
type: short-video | long-video | text | visual
core_idea: <одна фраза>
pillar: Деньги | Операционка | Маркетинг | Кейсы | Тренды
source: Anton | content-adapter | external-<название>
status: sketch | developed | adapted | archived
adapted_to: [telegram, tiktok, youtube, ...]  ← какие платформы уже взяли
---

# Ядро материала

## Главная мысль
<one-liner>

## Ключевые пункты
1. ...
2. ...

## Реальные цифры / кейсы
- Чек 2100₽
- Маржа 20-22%
- Филиалы: Острогожск, Семилуки, Рамонь

## Связанные идеи
- [[content/ideas/...]]

## Источник (если адаптация)
- knowledge-base/external-sources/...
```

---

## Навигация

- [short-video/](short-video/) — короткие видео-ядра
- [long-video/](long-video/) — длинные видео-ядра
- [text/](text/) — текстовые ядра
- [visual/](visual/) — визуальные ядра (карусели, инфографика)

---

## Правила

- **Один файл = одно ядро**. Не смешивай темы.
- **Всегда указывай `adapted_to`** — чтобы видеть какие платформы ещё не задействованы.
- **Не дублируй в platforms/**. Ядро хранится здесь, в platforms/ — готовая адаптация.
- **Если тема не взлетела на 2+ платформах** — архивируй (`status: archived`).
