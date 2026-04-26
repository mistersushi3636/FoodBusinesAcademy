from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from config import IDEA_STATUSES
from utils.markdown import list_idea_files


def ideas_status_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for status, label, path in IDEA_STATUSES:
        count = len(list_idea_files(path))
        text = f"{label} ({count})"
        builder.row(InlineKeyboardButton(text=text, callback_data=f"ideas_status:{status}"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_main"))
    return builder.as_markup()


def ideas_list_keyboard(status: str, ideas: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for idea_path in ideas[:20]:
        title = idea_path.stem[:40]
        builder.row(InlineKeyboardButton(text=f"📄 {title}", callback_data=f"idea:{status}:{idea_path.stem}"))
    builder.row(InlineKeyboardButton(text="◀️ К статусам", callback_data="my_ideas"))
    return builder.as_markup()


def idea_actions_keyboard(status: str, slug: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔍 Анализ", callback_data=f"action:analyze:{status}:{slug}"),
        InlineKeyboardButton(text="📅 Построить план", callback_data=f"action:plan:{status}:{slug}"),
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Доработать", callback_data=f"action:refine:{status}:{slug}"),
        InlineKeyboardButton(text="⚡ В работу", callback_data=f"action:start:{status}:{slug}"),
    )
    builder.row(
        InlineKeyboardButton(text="✅ Готово", callback_data=f"action:complete:{status}:{slug}"),
        InlineKeyboardButton(text="🗄️ В архив", callback_data=f"action:archive:{status}:{slug}"),
    )
    builder.row(InlineKeyboardButton(text="◀️ К списку", callback_data=f"ideas_status:{status}"))
    return builder.as_markup()


def confirm_keyboard(action: str, payload: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Да", callback_data=f"confirm:{action}:{payload}"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="back_to_main"),
    )
    return builder.as_markup()
