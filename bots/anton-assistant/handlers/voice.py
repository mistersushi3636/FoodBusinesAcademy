import tempfile
from pathlib import Path

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from loguru import logger

from config import settings, VOICE_INBOX
from keyboards.main_menu import main_menu, back_to_main
from services.whisper_local import transcribe
from services.vault_writer import save_new_idea
from services.claude_cli import analyze_idea_via_claude, run_claude_skill


router = Router(name="voice")


class VoiceStates(StatesGroup):
    waiting_voice = State()
    choosing_action = State()


def _is_anton(event) -> bool:
    return event.from_user.id == settings.anton_chat_id


@router.callback_query(F.data == "voice_to_post")
async def voice_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    text = (
        "🎙️ <b>Голос → пост</b>\n\n"
        "Пришли голосовое. Я расшифрую и спрошу что с ним сделать:\n"
        "  • превратить в пост Telegram\n"
        "  • в сценарий шортса\n"
        "  • просто записать как идею\n"
        "  • сохранить как заметку"
    )
    await callback.message.edit_text(text, reply_markup=back_to_main())
    await state.set_state(VoiceStates.waiting_voice)
    await callback.answer()


@router.message(F.voice)
async def receive_voice(message: Message, state: FSMContext, bot: Bot) -> None:
    if not _is_anton(message):
        return

    await message.answer("🎙️ Получил голосовое. Расшифровываю (10-30 сек)...")

    voice_file = await bot.get_file(message.voice.file_id)
    VOICE_INBOX.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = Path(tmp.name)

    try:
        await bot.download_file(voice_file.file_path, destination=str(tmp_path))
        text = await transcribe(tmp_path)
    except Exception as e:
        logger.error(f"Voice transcription failed: {e}")
        await message.answer(f"⚠️ Ошибка расшифровки: {e}")
        return
    finally:
        tmp_path.unlink(missing_ok=True)

    if not text or len(text.strip()) < 5:
        await message.answer("⚠️ Не удалось расшифровать (тишина или шум).", reply_markup=main_menu())
        await state.clear()
        return

    await state.update_data(transcript=text)
    await state.set_state(VoiceStates.choosing_action)

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💡 Как идея", callback_data="voice_action:idea"),
        InlineKeyboardButton(text="📝 Пост TG", callback_data="voice_action:tg_post"),
    )
    builder.row(
        InlineKeyboardButton(text="🎬 Шортс", callback_data="voice_action:short"),
        InlineKeyboardButton(text="📓 Заметка", callback_data="voice_action:note"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Отмена", callback_data="back_to_main"))

    await message.answer(
        f"📝 <b>Расшифровка:</b>\n\n<i>{text[:1500]}{'…' if len(text) > 1500 else ''}</i>\n\nЧто сделать?",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("voice_action:"))
async def voice_action(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    action = callback.data.split(":", 1)[1]
    data = await state.get_data()
    text = data.get("transcript", "")
    if not text:
        await callback.message.edit_text("Транскрипт потерян. Начни заново.", reply_markup=main_menu())
        await state.clear()
        return

    if action == "idea":
        path = await save_new_idea(text, source="telegram-voice")
        await callback.message.edit_text(f"💡 Идея сохранена. Анализирую...", reply_markup=back_to_main())
        try:
            result = await analyze_idea_via_claude(path)
            await callback.message.answer(f"🔍 Анализ:\n\n{result[:3500]}", reply_markup=main_menu())
        except Exception as e:
            await callback.message.answer(f"⚠️ Анализ не удался: {e}\nИдея сохранена в incoming.", reply_markup=main_menu())
    elif action == "tg_post":
        await callback.message.edit_text("📝 Делаю пост через /telegram-content...", reply_markup=back_to_main())
        try:
            result = await run_claude_skill("telegram-content", text)
            await callback.message.answer(f"✅ Готово:\n\n{result[:3500]}", reply_markup=main_menu())
        except Exception as e:
            await callback.message.answer(f"⚠️ Ошибка: {e}", reply_markup=main_menu())
    elif action == "short":
        await callback.message.edit_text("🎬 Делаю сценарий через /shortform-content...", reply_markup=back_to_main())
        try:
            result = await run_claude_skill("shortform-content", text)
            await callback.message.answer(f"✅ Готово:\n\n{result[:3500]}", reply_markup=main_menu())
        except Exception as e:
            await callback.message.answer(f"⚠️ Ошибка: {e}", reply_markup=main_menu())
    elif action == "note":
        from datetime import datetime
        from utils.markdown import write_markdown
        from utils.slug import timestamp_slug, slugify
        VOICE_INBOX.mkdir(parents=True, exist_ok=True)
        slug = slugify(text.split("\n")[0][:60])
        note_path = VOICE_INBOX / f"{timestamp_slug()}-{slug}.md"
        await write_markdown(
            note_path,
            {"type": "voice-note", "created": datetime.now().isoformat(), "source": "telegram"},
            text,
        )
        await callback.message.edit_text(f"📓 Заметка сохранена: <code>{note_path.name}</code>", reply_markup=main_menu())

    await state.clear()
    await callback.answer()
