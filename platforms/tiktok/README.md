---
name: TikTok Platform
description: Холодный охват — вертикальное видео, молодая аудитория, CTA в Telegram
type: platform
priority: high
---

# 🎵 TikTok — холодный охват

> Холодная аудитория. Первые 2 секунды решают всё. CTA → ссылка в био → Telegram.

**Агент-стратег:** [[agents/platform/tiktok|tiktok-agent]]
**Аккаунт:** *(будет указан при запуске)*

---

## Структура папки

```
tiktok/
├── README.md       ← этот файл
├── calendar.md     ← редплан TikTok
├── posts/          ← сценарии и описания
└── assets/         ← превью, субтитры
```

---

## Текущий ритм

- **3–5 видео/нед**
- Длина: 15–60 сек, оптимум 30–45 сек
- Субтитры обязательны
- Первые 2 сек: хук без вступления

---

## Готовые материалы

```dataview
TABLE WITHOUT ID
  file.link AS "Видео",
  pillar AS "Пиллар",
  publish_date AS "Дата",
  status AS "Статус"
FROM "platforms/tiktok/posts"
SORT publish_date DESC
```

---

## Правила

См. [[agents/platform/tiktok]] — хуки, субтитры, CTA, запреты.
