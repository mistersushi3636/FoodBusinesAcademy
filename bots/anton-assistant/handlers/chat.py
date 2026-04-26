import asyncio
from collections import deque
from typing import Deque, Dict, List

import anthropic
from aiogram import Router
from aiogram.enums import ChatAction
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message
from loguru import logger

from config import settings

router = Router()

# Per-chat conversation history: {chat_id: deque of {role, content}}
_history: Dict[int, Deque[dict]] = {}
MAX_HISTORY = 20  # messages (10 exchanges)

SYSTEM_PROMPT = """Ты личный ассистент Антона Коваленко — владельца сети доставки «Мистер Суши» (Воронеж, 4 точки) и автора проекта Food Business Academy.

Контекст бизнеса:
- Доставка суши и роллов, средний чек 2100₽, маржа 20-22%
- Точки: Воронеж (основная), Острогожск, Семилуки, Рамонь
- Личный бренд: эксперт по ресторанному бизнесу для других рестораторов
- 5 контент-пилларов: Деньги, Операционка, Маркетинг, Кейсы, Тренды

Правила:
- Отвечай на русском
- Кратко и конкретно, без воды и AI-клише
- Практические советы применительно к ресторанному бизнесу и его нише
- Помни контекст всего диалога"""


def _get_history(chat_id: int) -> Deque[dict]:
    if chat_id not in _history:
        _history[chat_id] = deque(maxlen=MAX_HISTORY)
    return _history[chat_id]


def _build_messages(chat_id: int, user_text: str) -> List[dict]:
    history = _get_history(chat_id)
    messages = list(history)
    messages.append({"role": "user", "content": user_text})
    return messages


async def _call_claude(messages: List[dict]) -> str:
    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    response = await client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text


async def _send_typing_loop(message: Message, stop_event: asyncio.Event) -> None:
    """Keep sending 'typing' action every 4s until stop_event is set."""
    while not stop_event.is_set():
        try:
            await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
        except Exception:
            pass
        try:
            await asyncio.wait_for(asyncio.shield(stop_event.wait()), timeout=4)
        except asyncio.TimeoutError:
            pass


@router.message(StateFilter(default_state), lambda m: m.text and m.text.startswith("/clear"))
async def clear_history(message: Message) -> None:
    _history.pop(message.chat.id, None)
    await message.answer("История диалога очищена.")


@router.message(StateFilter(default_state))
async def chat_with_claude(message: Message) -> None:
    if not message.text:
        return

    chat_id = message.chat.id
    user_text = message.text
    logger.info(f"Chat [{chat_id}]: {user_text[:80]}")

    stop_typing = asyncio.Event()
    typing_task = asyncio.create_task(_send_typing_loop(message, stop_typing))

    try:
        messages = _build_messages(chat_id, user_text)
        response_text = await asyncio.wait_for(_call_claude(messages), timeout=60)

        # Save to history
        history = _get_history(chat_id)
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": response_text})

        logger.info(f"Claude responded [{chat_id}]: {len(response_text)} chars")

    except asyncio.TimeoutError:
        response_text = "⚠️ Тайм-аут. Попробуй ещё раз."
        logger.error(f"Claude timeout for chat [{chat_id}]")
    except Exception as e:
        response_text = "⚠️ Ошибка. Попробуй ещё раз."
        logger.error(f"Claude error [{chat_id}]: {e}")
    finally:
        stop_typing.set()
        typing_task.cancel()

    # Split if over Telegram 4096 char limit
    if len(response_text) > 4096:
        for i in range(0, len(response_text), 4096):
            await message.answer(response_text[i:i + 4096])
    else:
        await message.answer(response_text)
