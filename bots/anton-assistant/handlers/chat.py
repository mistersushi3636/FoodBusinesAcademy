from aiogram import Router
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.enums import ChatAction
from aiogram.types import Message
from loguru import logger

from services.claude_cli import ask_claude

router = Router()

SYSTEM_CONTEXT = """Ты личный ассистент Антона Коваленко — владельца сети доставки «Мистер Суши» (Воронеж) и автора проекта Food Business Academy.

Контекст:
- Антон строит личный бренд эксперта по ресторанному бизнесу
- Основные темы: деньги, операционка, маркетинг, кейсы, тренды в HoReCa
- Средний чек 2100₽, маржа 20-22%, 4 точки (Воронеж, Острогожск, Семилуки, Рамонь)
- Рабочий vault в Obsidian: /Users/anton/FoodBusinesAcademy/

Правила:
- Отвечай на русском
- Кратко и конкретно, без воды
- Если вопрос про бизнес/контент/маркетинг — давай практические советы применительно к его нише
- Если нужно что-то сделать в файлах vault — скажи что именно нужно сделать"""


@router.message(StateFilter(default_state))
async def chat_with_claude(message: Message) -> None:
    if not message.text:
        return

    logger.info(f"Chat message: {message.text[:80]}")
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)

    prompt = f"{SYSTEM_CONTEXT}\n\nСообщение от Антона: {message.text}"
    response = await ask_claude(prompt, timeout=90)

    if not response:
        await message.answer("⚠️ Claude не ответил. Попробуй ещё раз.")
        return

    # Telegram limit 4096 chars
    if len(response) > 4096:
        for i in range(0, len(response), 4096):
            await message.answer(response[i:i+4096])
    else:
        await message.answer(response)
