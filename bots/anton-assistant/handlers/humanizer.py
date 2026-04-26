import tempfile
from pathlib import Path

from aiogram import Bot, F, Router
from aiogram.enums import ChatAction
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from loguru import logger

from keyboards.main_menu import back_to_main
from services.claude_cli import run_claude_skill
from services.whisper_local import transcribe

router = Router()


class HumanizerStates(StatesGroup):
    waiting_text = State()


@router.callback_query(F.data == "humanizer")
async def humanizer_start(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(HumanizerStates.waiting_text)
    await callback.message.edit_text(
        "✍️ <b>Гуманизатор текста</b>\n\n"
        "Пришли текст (или голосовое) — уберу AI-паттерны, сделаю живым и человеческим.\n\n"
        "<i>Работает на blader/humanizer (15k ⭐)</i>",
        reply_markup=back_to_main(),
    )
    await callback.answer()


@router.message(StateFilter(HumanizerStates.waiting_text), F.text)
async def humanize_text(message: Message, state: FSMContext) -> None:
    await state.clear()
    await _process_humanize(message, message.text)


@router.message(StateFilter(HumanizerStates.waiting_text), F.voice)
async def humanize_voice(message: Message, state: FSMContext, bot: Bot) -> None:
    await state.clear()
    await message.answer("🎙️ Расшифровываю...")

    voice_file = await bot.get_file(message.voice.file_id)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        await bot.download_file(voice_file.file_path, destination=str(tmp_path))
        text = await transcribe(tmp_path)
    finally:
        tmp_path.unlink(missing_ok=True)

    if not text:
        await message.answer("⚠️ Не удалось распознать голос.", reply_markup=back_to_main())
        return

    await message.answer(f"🎙️ Распознано:\n<i>{text}</i>")
    await _process_humanize(message, text)


async def _process_humanize(message: Message, text: str) -> None:
    await message.bot.send_chat_action(message.chat.id, ChatAction.TYPING)
    logger.info(f"Humanizing {len(text)} chars")

    prompt = (
        "Гуманизируй следующий текст: убери AI-паттерны, сделай его живым, "
        "естественным, человеческим. Сохрани смысл и тон. "
        "Верни ТОЛЬКО готовый текст без пояснений.\n\n"
        f"{text}"
    )

    result = await run_claude_skill("humanizer", prompt, timeout=180)

    if not result:
        await message.answer("⚠️ Ошибка гуманизации. Попробуй ещё раз.", reply_markup=back_to_main())
        return

    await message.answer(
        f"✅ <b>Готово:</b>\n\n{result}",
        reply_markup=back_to_main(),
    )
