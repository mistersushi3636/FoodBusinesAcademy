#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=== Anton Assistant Bot — установка ==="
echo ""

# Проверить Python
if ! command -v python3 &>/dev/null; then
    echo "❌ Python 3 не найден. Установи: brew install python"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $PYTHON_VERSION"

# Проверить ffmpeg
if ! command -v ffmpeg &>/dev/null; then
    echo "⚠️  ffmpeg не найден. Whisper без него не работает."
    echo "   Установи: brew install ffmpeg"
    echo "   Продолжаем без него (транскрипция голосовых не будет работать)."
fi

# Виртуальное окружение
if [ ! -d ".venv" ]; then
    echo "→ Создаю виртуальное окружение..."
    python3 -m venv .venv
    echo "✓ .venv создан"
else
    echo "✓ .venv уже существует"
fi

# Активация и установка зависимостей
source .venv/bin/activate
echo "→ Устанавливаю зависимости..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "✓ Зависимости установлены"

# Создать .env если нет
if [ ! -f ".env" ]; then
    cat > .env << 'EOF'
# Telegram Bot Token (получить у @BotFather)
BOT_TOKEN=your_bot_token_here

# Твой Telegram user ID (узнать у @userinfobot)
ANTON_CHAT_ID=your_telegram_id_here

# Путь к Obsidian vault
VAULT_PATH=/Users/anton/Food Business Academy
EOF
    echo "✓ .env создан — заполни BOT_TOKEN и ANTON_CHAT_ID"
else
    echo "✓ .env уже существует"
fi

# Создать папку логов
mkdir -p logs

# Создать inbox директорию в vault
VAULT_PATH="/Users/anton/Food Business Academy"
INBOX_DIR="$VAULT_PATH/bots/anton-assistant/inbox"
PROCESSED_DIR="$INBOX_DIR/.processed"
mkdir -p "$INBOX_DIR" "$PROCESSED_DIR"
echo "✓ Inbox директория: $INBOX_DIR"

# Создать папки ideas-bot если нет
for folder in incoming analyzing refined planned in-progress completed archived; do
    mkdir -p "$VAULT_PATH/ideas-bot/$folder"
done
echo "✓ ideas-bot/ папки готовы"

echo ""
echo "=== Готово! ==="
echo ""
echo "Следующие шаги:"
echo "1. Заполни .env (BOT_TOKEN и ANTON_CHAT_ID)"
echo "2. Тест: source .venv/bin/activate && python bot.py"
echo "3. Автозапуск:"
echo "   cp com.fba.anton-assistant.plist ~/Library/LaunchAgents/"
echo "   launchctl load ~/Library/LaunchAgents/com.fba.anton-assistant.plist"
echo "   launchctl start com.fba.anton-assistant"
