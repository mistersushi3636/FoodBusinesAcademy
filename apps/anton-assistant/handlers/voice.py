"""
Voice handler: downloads voice → Whisper API transcription → orchestrator pipeline.
"""
import tempfile
from pathlib import Path

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from config import settings, TRANSCRIPTS_INBOX
from keyboards.main_menu import main_menu, back_to_main

router = Router(name="voice")


class VoiceStates(StatesGroup):
    choosing_action = State()


def _is_anton(event) -> bool:
    return event.from_user.id == settings.anton_chat_id


@router.message(F.voice)
async def receive_voice(message: Message, state: FSMContext, bot: Bot) -> None:
    if not _is_anton(message):
        return

    await message.answer("🎙️ Получил. Расшифровываю через Whisper API...")

    # Download voice file
    voice_file = await bot.get_file(message.voice.file_id)
    TRANSCRIPTS_INBOX.mkdir(parents=True, exist_ok=True)

    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False, dir=TRANSCRIPTS_INBOX) as tmp:
        tmp_path = Path(tmp.name)

    try:
        await bot.download_file(voice_file.file_path, destination=str(tmp_path))

        from apps.shared.openai_client import transcribe_audio
        text = await transcribe_audio(
            api_key=settings.openai_api_key,
            audio_path=tmp_path,
            language="ru",
        )
    except Exception as e:
        logger.error(f"Voice transcription failed: {e}")
        await message.answer(f"⚠️ Ошибка расшифровки: {e}")
        tmp_path.unlink(missing_ok=True)
        return
    finally:
        tmp_path.unlink(missing_ok=True)

    if not text or len(text.strip()) < 5:
        await message.answer("⚠️ Не удалось расшифровать (тишина или шум).", reply_markup=main_menu())
        await state.clear()
        return

    await state.update_data(transcript=text)
    await state.set_state(VoiceStates.choosing_action)

    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🚀 Полный пайплайн", callback_data="voice_action:pipeline"),
        InlineKeyboardButton(text="📝 Только пост TG", callback_data="voice_action:tg_post"),
    )
    builder.row(
        InlineKeyboardButton(text="🎬 Только шортс", callback_data="voice_action:short"),
        InlineKeyboardButton(text="📓 Записать как идею", callback_data="voice_action:idea"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Отмена", callback_data="back_to_main"))

    preview = text[:1000] + ("…" if len(text) > 1000 else "")
    await message.answer(
        f"📝 <b>Расшифровка:</b>\n\n<i>{preview}</i>\n\n"
        f"Что сделать?\n"
        f"<b>Полный пайплайн</b> = TG+IG+YT драфты + картинка + тебе на апрув",
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
    await state.clear()

    if not text:
        await callback.message.edit_text("Транскрипт потерян. Начни заново.", reply_markup=main_menu())
        await callback.answer()
        return

    if action == "pipeline":
        await callback.message.edit_text(
            "🚀 Запускаю полный пайплайн: TG + IG + YT черновики + картинка...\n"
            "Пришлю все на апрув отдельными сообщениями (~1-2 мин).",
            reply_markup=back_to_main(),
        )
        try:
            import orchestrator
            task_id = await orchestrator.handle_text(text)
            await callback.message.answer(
                f"✅ Задача #{task_id} в работе. Черновики придут в личку.",
                reply_markup=main_menu(),
            )
        except Exception as e:
            logger.error(f"Pipeline error: {e}")
            await callback.message.answer(f"⚠️ Ошибка пайплайна: {e}", reply_markup=main_menu())

    elif action == "tg_post":
        await callback.message.edit_text("📝 Делаю TG-пост...", reply_markup=back_to_main())
        try:
            from skills.draft import run as draft
            result = await draft(content=text, platform="telegram", api_key=settings.anthropic_api_key)
            await callback.message.answer(f"✅ Черновик TG:\n\n{result}", reply_markup=main_menu())
        except Exception as e:
            await callback.message.answer(f"⚠️ Ошибка: {e}", reply_markup=main_menu())

    elif action == "short":
        await callback.message.edit_text("🎬 Делаю сценарий шортса...", reply_markup=back_to_main())
        try:
            from skills.draft import run as draft
            result = await draft(content=text, platform="youtube", api_key=settings.anthropic_api_key)
            await callback.message.answer(f"✅ Сценарий Shorts:\n\n{result}", reply_markup=main_menu())
        except Exception as e:
            await callback.message.answer(f"⚠️ Ошибка: {e}", reply_markup=main_menu())

    elif action == "idea":
        try:
            from skills.capture import run as capture
            idea = await capture(raw_text=text, api_key=settings.anthropic_api_key, source_type="voice")
            await callback.message.edit_text(
                f"💡 Идея сохранена:\n\n"
                f"<b>Суть:</b> {idea['core_idea']}\n"
                f"<b>Пиллар:</b> {idea['pillar']}\n"
                f"<b>Формат:</b> {idea['recommended_format']}\n"
                f"<b>Файл:</b> <code>{Path(idea['transcript_file']).name}</code>",
                reply_markup=main_menu(),
            )
        except Exception as e:
            await callback.message.answer(f"⚠️ Ошибка: {e}", reply_markup=main_menu())

    await callback.answer()


@router.callback_query(F.data.startswith("done:"))
async def task_done(callback: CallbackQuery) -> None:
    """Anton confirmed manual publication for IG/YT."""
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    parts = callback.data.split(":")
    task_id, platform = int(parts[1]), parts[2]
    import orchestrator
    await orchestrator.handle_approve(task_id, platform)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer(f"✅ {platform} — отмечено как опубликовано")


@router.callback_query(F.data.startswith("cancel:"))
async def task_cancel(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    task_id = int(callback.data.split(":")[1])
    import orchestrator
    await orchestrator.handle_cancel(task_id)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.answer("Задача отменена.")
