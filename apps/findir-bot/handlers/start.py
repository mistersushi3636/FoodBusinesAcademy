from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from config import is_authorized, is_owner

router = Router()


def main_kb(owner: bool) -> ReplyKeyboardMarkup:
    rows = [
        [KeyboardButton(text="💰 Внести выручку"), KeyboardButton(text="🛒 Расходы за день")],
        [KeyboardButton(text="➕ Доп. расход за день")],
    ]
    if owner:
        rows.append([KeyboardButton(text="📅 Месячный расход"), KeyboardButton(text="👥 Выплата ФОТ")])
    rows.append([KeyboardButton(text="📊 Сводка"), KeyboardButton(text="ℹ️ Помощь")])
    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


@router.message(CommandStart())
async def start_handler(message: Message):
    if not is_authorized(message.from_user.id):
        await message.answer(
            "🚫 Доступ запрещён.\n"
            f"Ваш TG ID: <code>{message.from_user.id}</code>\n"
            "Передайте этот ID Антону для добавления в систему."
        )
        return
    role = "Владелец" if is_owner(message.from_user.id) else "Управляющий"
    await message.answer(
        f"🍣 <b>MR.SUSHI Финдир-бот</b>\n\n"
        f"Привет, {message.from_user.first_name}!\n"
        f"Роль: <b>{role}</b>\n\n"
        f"Дашборд: https://findir.mistersushi36.pro\n\n"
        f"Выбери действие на клавиатуре ниже:",
        reply_markup=main_kb(is_owner(message.from_user.id)),
    )


@router.message(Command("help"))
@router.message(lambda m: m.text and m.text.startswith("ℹ️"))
async def help_handler(message: Message):
    if not is_authorized(message.from_user.id):
        return
    text = (
        "<b>Команды:</b>\n"
        "/start — главное меню\n"
        "/daily — внести выручку и фикс. расходы за день\n"
        "/extra — добавить ad-hoc расход за день (еда персонала, разовый и т.д.)\n"
        "/summary — сводка по текущему месяцу\n"
    )
    if is_owner(message.from_user.id):
        text += "/monthly — внести месячный расход\n"
    await message.answer(text)
