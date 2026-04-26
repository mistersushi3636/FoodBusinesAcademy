# Content-assistant (личный бот Антона)

Telegram-бот для Антона: голосовое → готовый пост + идеи шортсов + тезисы видео.

**Статус:** заготовка (план в [../README.md](../README.md)).

## Когда разрабатываем

Первая итерация — неделя 1–2 запуска проекта (главный рычаг продуктивности).

**Альтернатива на старте:** пока бот не готов, использовать локальные Claude-скиллы из [../../.claude/skills/](../../.claude/skills/) — `voice-to-post`, `repurpose`, `content-idea`.

## Что нужно перед стартом разработки

- [ ] Решить: Whisper API или whisper.cpp локально (cost vs. setup)
- [ ] Получить ключи: Anthropic API, OpenAI (если Whisper API)
- [ ] Подготовить шаблон промптов из `tone-of-voice.md` и `pillars.md`
- [ ] Whitelist user_id Антона

## Архитектура (черновик)

```
voice msg → aiogram → [Whisper] → transcript.md → 
  → save to knowledge-base/transcripts/ →
  → Claude API (with cached system prompt: tone + pillars) →
  → return: [Telegram post] + [3 shorts hooks] + [video outline]
```

## Файлы (когда начнём)

- `bot.py`
- `transcribe.py` — Whisper интеграция
- `generate.py` — Claude API + prompt caching
- `prompts/` — system prompts (загружаются из brand/ и content/)
- `requirements.txt`
- `.env.example`
