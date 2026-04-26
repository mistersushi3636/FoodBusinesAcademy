from typing import List, Dict, Any

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder


def planner_main_menu() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Новая задача", callback_data="planner_new"),
        InlineKeyboardButton(text="📋 Сегодня", callback_data="planner_today"),
    )
    builder.row(
        InlineKeyboardButton(text="📅 Все задачи", callback_data="planner_all"),
        InlineKeyboardButton(text="⚙️ Настройки", callback_data="planner_settings"),
    )
    builder.row(InlineKeyboardButton(text="◀️ Главное меню", callback_data="back_to_main"))
    return builder.as_markup()


def task_confirm_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Сохранить", callback_data="planner_confirm_save"),
        InlineKeyboardButton(text="✏️ Изменить", callback_data="planner_confirm_edit"),
    )
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="planner_menu"))
    return builder.as_markup()


def task_detail_keyboard(task_id: int, remind_1h: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Выполнено", callback_data=f"task_done:{task_id}"),
        InlineKeyboardButton(text="⏰ Перенести", callback_data=f"task_voice_edit:{task_id}"),
    )
    remind_text = "🔕 Выкл напоминание" if remind_1h else "🔔 Вкл напоминание"
    remind_cb = f"task_remind_off:{task_id}" if remind_1h else f"task_remind_on:{task_id}"
    builder.row(
        InlineKeyboardButton(text="🎙️ Голосом изменить", callback_data=f"task_voice_edit:{task_id}"),
        InlineKeyboardButton(text=remind_text, callback_data=remind_cb),
    )
    builder.row(InlineKeyboardButton(text="🗑 Удалить", callback_data=f"task_delete:{task_id}"))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="planner_today"))
    return builder.as_markup()


def tasks_list_keyboard(tasks: List[Dict[str, Any]], back_cb: str = "planner_menu") -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for task in tasks[:20]:
        prefix = "⭐" if task["is_important"] else "✦"
        tm = f"{task['task_time']} " if task.get("task_time") else ""
        label = f"{prefix} {tm}{task['title'][:38]}"
        builder.row(InlineKeyboardButton(
            text=label, callback_data=f"task_view:{task['id']}"
        ))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data=back_cb))
    return builder.as_markup()


def task_reminder_keyboard(task_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Понял", callback_data=f"task_done:{task_id}"),
        InlineKeyboardButton(text="⏰ +30 мин", callback_data=f"task_snooze:{task_id}:30"),
    )
    builder.row(
        InlineKeyboardButton(text="🔕 Выкл напоминания", callback_data=f"task_remind_off:{task_id}")
    )
    return builder.as_markup()


def planner_settings_keyboard(notifications_enabled: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if notifications_enabled:
        builder.row(InlineKeyboardButton(
            text="🔕 Выключить все напоминания", callback_data="planner_notif_off"
        ))
    else:
        builder.row(InlineKeyboardButton(
            text="🔔 Включить все напоминания", callback_data="planner_notif_on"
        ))
    builder.row(InlineKeyboardButton(text="◀️ Назад", callback_data="planner_menu"))
    return builder.as_markup()
