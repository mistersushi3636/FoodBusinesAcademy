"""
Chat handler: multi-turn conversation with Claude via Anthropic API.
History stored in SQLite, system prompt cached for token savings.
"""
import asyncio
from pathlib import Path

from aiogram import Router
from aiogram.enums import ChatAction
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message
from loguru import logger

from config import settings
from apps.shared.anthropic_client import ask_with_history
from apps.shared.memory import save_message, get_history

router = Router(name="chat")

DB_PATH = Path(__file__).parents[1] / "fba.db"

SYSTEM_PROMPT = """Ты личный ассистент Антона Коваленко — владельца «Мистер Суши» (Воронеж) и автора Food Business Academy.

Бизнес-контекст:
- Доставка суши, средний чек 2100₽, маржа 20-22%
- Точки: Воронеж, Острогожск (30 тыс. жителей, +4 мес в плюс), Семилуки (20 тыс., работает), Рамонь (15 тыс., закрыл через год)
- Личный бренд: эксперт для рестораторов, без инфоцыганщины
- 5 контент-пилларов: Деньги 30% / Операционка 20% / Маркетинг 20% / Кейсы 20% / Тренды 10%
- Площадки: Telegram (главный хаб) + Instagram + YouTube

Правила ответов:
- Русский язык, кратко и конкретно
- Практические советы применительно к ресторанному бизнесу
- Не «можно рассмотреть», а «сделай X потому что Y»
- Числа и примеры где возможно
"""


async def _typing_loop(message: Message, stop: asyncio.Event) -> None:
    while not stop.is_set():
        try:
            await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        except Exception:
            pass
        try:
            await asyncio.wait_for(asyncio.shield(stop.wait()), timeout=4)
        except asyncio.TimeoutError:
            pass


@router.message(StateFilter(default_state), lambda m: m.text and m.text == "/clear")
async def clear_history(message: Message) -> None:
    # Mark all history as cleared by inserting a sentinel — simplest approach
    # (actual rows stay, just reset by ignoring old ones via new /clear marker)
    conn = __import__("sqlite3").connect(str(DB_PATH))
    conn.execute("DELETE FROM conversations WHERE chat_id=?", (message.chat.id,))
    conn.commit()
    conn.close()
    await message.answer("История диалога очищена. 🗑️")


@router.message(StateFilter(default_state))
async def chat_with_claude(message: Message) -> None:
    if not message.text:
        return

    chat_id = message.chat.id
    user_text = message.text
    logger.info(f"Chat [{chat_id}]: {user_text[:80]}")

    stop = asyncio.Event()
    typing_task = asyncio.create_task(_typing_loop(message, stop))

    try:
        # Load history from SQLite
        history = get_history(DB_PATH, chat_id, limit=20)
        history.append({"role": "user", "content": user_text})

        response = await ask_with_history(
            api_key=settings.anthropic_api_key,
            system=SYSTEM_PROMPT,
            messages=history,
            max_tokens=1500,
            cache_system=True,
        )

        if response:
            # Persist to SQLite
            save_message(DB_PATH, chat_id, "user", user_text)
            save_message(DB_PATH, chat_id, "assistant", response)
            logger.info(f"Claude replied [{chat_id}]: {len(response)} chars")
        else:
            response = "⚠️ Нет ответа. Попробуй ещё раз."
            logger.warning(f"Empty response [{chat_id}]")

    except Exception as e:
        response = "⚠️ Ошибка. Попробуй ещё раз."
        logger.error(f"Chat error [{chat_id}]: {e}")
    finally:
        stop.set()
        typing_task.cancel()

    # Split long messages
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await message.answer(response[i : i + 4096])
    else:
        await message.answer(response)
