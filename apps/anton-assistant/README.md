# Anton Assistant Bot

Персональный Telegram-бот Антона для работы с идеями, контентом и метриками FBA.

## Возможности

- **💡 Новая идея** — текст → анализ через Claude → сохранение в vault
- **📋 Мои идеи** — просмотр и управление идеями по статусам
- **📅 Контент-план** — текущий недельный план от content-marketer
- **📊 Метрики** — ввод цифр за неделю (просмотры, лайки, подписчики)
- **🎙️ Голос → пост** — голосовое → Whisper → выбор: идея / пост TG / шортс / заметка
- **Уведомления** — Claude Code сбрасывает сообщения в inbox/, бот отправляет Антону

## Требования

- Python 3.11+
- macOS (для LaunchAgent автозапуска)
- [ffmpeg](https://ffmpeg.org/) (нужен для faster-whisper)
- Telegram бот токен (получить у [@BotFather](https://t.me/BotFather))
- Твой Telegram user ID

## Установка

### 1. Создать бота у BotFather

1. Открой [@BotFather](https://t.me/BotFather) в Telegram
2. Отправь `/newbot`
3. Имя: `Anton FBA Assistant`
4. Username: `anton_fba_bot` (или любой свободный)
5. Сохрани токен вида `1234567890:ABCdef...`

### 2. Узнать свой Telegram ID

Напиши [@userinfobot](https://t.me/userinfobot) — он пришлёт твой `id`.

### 3. Запустить install.sh

```bash
cd "/Users/anton/Food Business Academy/bots/anton-assistant"
chmod +x install.sh
./install.sh
```

Скрипт создаст виртуальное окружение, установит зависимости, создаст `.env`.

### 4. Заполнить .env

```bash
nano .env
```

```env
BOT_TOKEN=1234567890:ABCdef...    # токен от BotFather
ANTON_CHAT_ID=123456789           # твой Telegram ID
VAULT_PATH=/Users/anton/Food Business Academy
```

### 5. Скачать модель Whisper

При первом запуске модель `medium` (~1.5GB) скачается автоматически.
Или заранее:
```bash
source .venv/bin/activate
python -c "from faster_whisper import WhisperModel; WhisperModel('medium', device='cpu', compute_type='int8')"
```

### 6. Установить ffmpeg (если нет)

```bash
brew install ffmpeg
```

### 7. Тест-запуск

```bash
source .venv/bin/activate
python bot.py
```

Открой Telegram → найди своего бота → отправь `/start`.

### 8. Автозапуск через LaunchAgent

```bash
cp com.fba.anton-assistant.plist ~/Library/LaunchAgents/
launchctl load ~/Library/LaunchAgents/com.fba.anton-assistant.plist
launchctl start com.fba.anton-assistant
```

Проверить статус:
```bash
launchctl list | grep fba
```

## Структура файлов

```
bots/anton-assistant/
├── bot.py                    # точка входа, Dispatcher
├── config.py                 # настройки (pydantic-settings)
├── requirements.txt          # зависимости
├── .env                      # токены (не в git!)
├── install.sh                # установка
├── com.fba.anton-assistant.plist  # macOS LaunchAgent
├── logs/                     # логи бота
├── handlers/
│   ├── start.py             # /start, главное меню
│   ├── ideas.py             # управление идеями
│   ├── metrics.py           # ввод метрик
│   ├── voice.py             # голосовые сообщения
│   ├── plans.py             # просмотр планов
│   └── notifications.py     # inbox watcher + callbacks
├── keyboards/
│   ├── main_menu.py         # главное меню
│   └── ideas_menu.py        # меню идей
├── services/
│   ├── whisper_local.py     # faster-whisper транскрипция
│   ├── vault_writer.py      # запись в Obsidian vault
│   └── claude_cli.py        # вызов claude CLI
└── utils/
    ├── slug.py              # транслитерация + слаги
    └── markdown.py          # чтение/запись markdown с frontmatter
```

## Как работает inbox

Claude Code агенты кладут JSON-файлы в:
```
vault/bots/anton-assistant/inbox/*.json
```

Формат:
```json
{
  "type": "plan_ready",
  "text": "Текст уведомления",
  "buttons": [
    {"text": "✅ ОК", "callback_data": "plan_ok"},
    {"text": "✏️ Правки", "callback_data": "plan_revise"}
  ]
}
```

Бот проверяет inbox каждые 5 секунд и отправляет Антону.

## Управление LaunchAgent

```bash
# Остановить
launchctl stop com.fba.anton-assistant

# Запустить
launchctl start com.fba.anton-assistant

# Выгрузить (не будет запускаться автоматически)
launchctl unload ~/Library/LaunchAgents/com.fba.anton-assistant.plist

# Загрузить снова
launchctl load ~/Library/LaunchAgents/com.fba.anton-assistant.plist

# Посмотреть логи
tail -f "/Users/anton/Food Business Academy/bots/anton-assistant/logs/bot.log"
```

## Обновление кода

```bash
launchctl stop com.fba.anton-assistant
# ... внести изменения ...
launchctl start com.fba.anton-assistant
```
