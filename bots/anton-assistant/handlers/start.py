from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery
from loguru import logger

from config import settings
from keyboards.main_menu import main_menu


router = Router(name="start")


def _is_anton(message_or_callback) -> bool:
    user_id = message_or_callback.from_user.id
    return user_id == settings.anton_chat_id


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not _is_anton(message):
        await message.answer("Бот персональный, доступ только владельцу.")
        logger.warning(f"Unauthorized access attempt by {message.from_user.id} (@{message.from_user.username})")
        return

    text = (
        "👋 Антон, привет.\n\n"
        "Я — твой бизнес-ассистент. Помогаю записывать идеи, дорабатывать их, "
        "строить планы реализации, отвечать на вопросы по проекту FBA.\n\n"
        "Что делаем?"
    )
    await message.answer(text, reply_markup=main_menu())


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    await callback.message.edit_text("Главное меню. Что делаем?", reply_markup=main_menu())
    await callback.answer()


@router.callback_query(F.data == "settings")
async def settings_menu(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    text = (
        "⚙️ <b>Настройки</b>\n\n"
        f"Vault: <code>{settings.vault_path}</code>\n"
        f"Whisper: <b>{settings.whisper_model}</b> ({settings.whisper_compute_type})\n"
        f"Уведомления: <b>{'вкл' if settings.notifications_enabled else 'выкл'}</b>\n\n"
        "Изменения через .env файл бота → перезапуск."
    )
    from keyboards.main_menu import back_to_main as kb_back
    await callback.message.edit_text(text, reply_markup=kb_back())
    await callback.answer()
