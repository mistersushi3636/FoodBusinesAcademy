import asyncio
from collections import deque
from typing import Deque, Dict

from aiogram import Router
from aiogram.enums import ChatAction
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message
from loguru import logger

from services.claude_cli import ask_claude

router = Router()

# Per-chat history: {chat_id: deque of (role, text)}
_history: Dict[int, Deque[tuple]] = {}
MAX_HISTORY = 10  # exchanges (20 messages)

SYSTEM_PROMPT = """Ты личный ассистент Антона Коваленко — владельца «Мистер Суши» (Воронеж, 4 точки) и автора проекта Food Business Academy.

Бизнес-контекст:
- Доставка суши, средний чек 2100₽, маржа 20-22%
- Точки: Воронеж, Острогожск, Семилуки, Рамонь
- Личный бренд: эксперт по ресторанному бизнесу
- 5 контент-пилларов: Деньги, Операционка, Маркетинг, Кейсы, Тренды

Правила:
- Отвечай на русском, кратко и конкретно
- Практические советы применительно к ресторанному бизнесу
- Учитывай контекст всего диалога ниже"""


def _get_history(chat_id: int) -> Deque[tuple]:
    if chat_id not in _history:
        _history[chat_id] = deque(maxlen=MAX_HISTORY * 2)
    return _history[chat_id]


def _build_prompt(chat_id: int, user_text: str) -> str:
    history = _get_history(chat_id)
    parts = [SYSTEM_PROMPT]

    if history:
        parts.append("\n[История диалога]")
        for role, text in history:
            label = "Антон" if role == "user" else "Ассистент"
            parts.append(f"{label}: {text}")

    parts.append(f"\n[Текущее сообщение]\nАнтон: {user_text}\nАссистент:")
    return "\n".join(parts)


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
    _history.pop(message.chat.id, None)
    await message.answer("История диалога очищена.")


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
        prompt = _build_prompt(chat_id, user_text)
        response = await ask_claude(prompt, timeout=120)

        if response:
            history = _get_history(chat_id)
            history.append(("user", user_text))
            history.append(("assistant", response))
            logger.info(f"Claude replied [{chat_id}]: {len(response)} chars")
        else:
            response = "⚠️ Нет ответа от Claude. Попробуй ещё раз."
            logger.warning(f"Empty Claude response [{chat_id}]")

    except Exception as e:
        response = "⚠️ Ошибка. Попробуй ещё раз."
        logger.error(f"Chat error [{chat_id}]: {e}")
    finally:
        stop.set()
        typing_task.cancel()

    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await message.answer(response[i:i + 4096])
    else:
        await message.answer(response)
