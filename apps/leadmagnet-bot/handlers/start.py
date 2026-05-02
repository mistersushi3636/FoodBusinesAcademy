"""
Lead-magnet bot: /start → check channel subscription → send PDF.
Flow:
  1. User sends /start
  2. Bot checks if user is subscribed to FBA channel
  3. If subscribed → send PDF immediately
  4. If not → show "subscribe" button → on callback re-check → send PDF
"""
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart
from aiogram.types import (
    CallbackQuery, FSInputFile, InlineKeyboardButton,
    InlineKeyboardMarkup, Message,
)
from loguru import logger

from config import settings

router = Router(name="start")

SUBSCRIBE_KEYBOARD = InlineKeyboardMarkup(inline_keyboard=[[
    InlineKeyboardButton(
        text="📢 Подписаться на канал",
        url=f"https://t.me/{settings.channel_id.lstrip('@')}",
    ),
    InlineKeyboardButton(
        text="✅ Я подписался",
        callback_data="check_sub",
    ),
]])


class SubCheckError(Exception):
    """Бот не имеет доступа к списку участников канала."""


async def _is_subscribed(bot: Bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(settings.channel_id, user_id)
        return member.status not in ("left", "kicked", "banned")
    except Exception as e:
        msg = str(e).lower()
        if "member list is inaccessible" in msg or "chat not found" in msg:
            logger.error(
                f"Bot не админ канала {settings.channel_id}. "
                f"Добавь @FBA_leadbot админом канала."
            )
            raise SubCheckError() from e
        logger.warning(f"Subscription check failed for {user_id}: {e}")
        return False


async def _send_lead_magnet(message_or_callback, bot: Bot) -> None:
    """Send the PDF to the user."""
    if isinstance(message_or_callback, CallbackQuery):
        chat_id = message_or_callback.from_user.id
        answer_fn = message_or_callback.message.answer
    else:
        chat_id = message_or_callback.chat.id
        answer_fn = message_or_callback.answer

    pdf_path = settings.lead_magnet_file

    if not pdf_path.exists():
        await answer_fn(
            "⚠️ Файл временно недоступен. Напиши в канал — пришлём вручную:\n"
            f"https://t.me/{settings.channel_id.lstrip('@')}"
        )
        logger.warning(f"PDF not found: {pdf_path}")
        return

    await bot.send_document(
        chat_id=chat_id,
        document=FSInputFile(path=str(pdf_path), filename="checklist-10-oshibok-FBA.pdf"),
        caption=settings.lead_magnet_caption,
    )
    logger.info(f"PDF sent to user {chat_id}")


SETUP_ERR = (
    "⚙️ Бот не подключён к каналу как администратор.\n\n"
    "Владельцу: добавь <b>@FBA_leadbot</b> в админы канала "
    "<b>@Food_Busines_Academy</b> с правом «Управление подписчиками» "
    "и попробуй снова."
)


@router.message(CommandStart())
async def cmd_start(message: Message, bot: Bot) -> None:
    user_id = message.from_user.id
    logger.info(f"/start from {user_id} (@{message.from_user.username})")

    try:
        is_sub = await _is_subscribed(bot, user_id)
    except SubCheckError:
        await message.answer(SETUP_ERR)
        return

    if is_sub:
        await message.answer(
            "👋 Привет! Ты подписан на <b>Food Business Academy</b>.\n"
            "Отправляю чек-лист прямо сейчас 👇"
        )
        await _send_lead_magnet(message, bot)
    else:
        await message.answer(
            "👋 Привет!\n\n"
            "Чтобы получить <b>Чек-лист: 10 ошибок при открытии доставки</b> — "
            "подпишись на канал Food Business Academy.\n\n"
            "После подписки нажми <b>«Я подписался»</b> 👇",
            reply_markup=SUBSCRIBE_KEYBOARD,
        )


@router.callback_query(F.data == "check_sub")
async def check_subscription(callback: CallbackQuery, bot: Bot) -> None:
    user_id = callback.from_user.id

    try:
        is_sub = await _is_subscribed(bot, user_id)
    except SubCheckError:
        await callback.message.answer(SETUP_ERR)
        await callback.answer()
        return

    if is_sub:
        await callback.message.edit_text(
            "✅ Подписка подтверждена! Отправляю чек-лист 👇"
        )
        await _send_lead_magnet(callback, bot)
    else:
        await callback.answer(
            "Ты ещё не подписан. Подпишись и нажми кнопку снова.",
            show_alert=True,
        )
