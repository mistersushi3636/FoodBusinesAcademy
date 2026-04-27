from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="💡 Новая идея", callback_data="new_idea"),
        InlineKeyboardButton(text="📋 Мои идеи", callback_data="my_ideas"),
    )
    builder.row(
        InlineKeyboardButton(text="📅 Контент-план", callback_data="content_plan"),
        InlineKeyboardButton(text="📊 Метрики", callback_data="enter_metrics"),
    )
    builder.row(
        InlineKeyboardButton(text="🎙️ Голос → пост", callback_data="voice_to_post"),
        InlineKeyboardButton(text="📆 Планер", callback_data="planner_menu"),
    )
    builder.row(
        InlineKeyboardButton(text="✍️ Гуманизатор", callback_data="humanizer"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings"),
    )
    return builder.as_markup()


def back_to_main() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main"))
    return builder.as_markup()
