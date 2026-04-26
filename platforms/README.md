---
name: Platforms
description: Готовые адаптированные материалы по каждой платформе
type: hub
---

# 📱 Platforms — площадки и их материалы

> Каждая папка платформы содержит финальные материалы, готовые к публикации или уже опубликованные. Планы и редплан — в `platforms/<name>/calendar.md`.

---

## Главный хаб: [🔷 Telegram](telegram/)

Все остальные платформы ведут аудиторию сюда.

---

## Приоритетные каналы охвата

- [🎵 TikTok](tiktok/) — холодный охват, вертикальное видео
- [📸 Instagram](instagram/) — Reels + карусели + Stories
- [📺 YouTube](youtube/) — глубокая экспертиза + Shorts

## Вторичные каналы

- [🔵 ВКонтакте](vk/) — регионы, возраст 30+
- [📰 Дзен](dzen/) — SEO-хвост
- [🧵 Threads](threads/) — короткие касания
- [💬 MAX](max/) — зеркало TG

---

## Структура каждой платформы

```
platforms/<name>/
├── strategy.md      ← стратегия платформы (из agents/platform/<name>.md)
├── calendar.md      ← редплан платформы
├── posts/ или соответствующая папка
│   └── YYYY-MM-DD-название.md
├── assets/          ← визуалы
└── metrics.md       ← метрики (обновляет analytics)
```

---

## Правила

- Финальные материалы — здесь
- Ядра материалов — в [content-bank](../content-bank/)
- Правила адаптации — в [agents/platform/](../agents/platform/)
- Визуальные шаблоны — в [design-system](../design-system/)
