import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from aiogram import Router, F, Bot
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery
from loguru import logger

from config import settings
from keyboards.main_menu import main_menu, back_to_main
from keyboards.planner_menu import (
    planner_main_menu, task_confirm_keyboard, task_detail_keyboard,
    tasks_list_keyboard, planner_settings_keyboard,
)
from services.planner_db import (
    add_task, get_task, get_tasks_for_date, get_overdue_tasks,
    get_all_pending, mark_done, update_task, delete_task,
    get_setting, set_setting,
)
from services.task_parser import parse_task_from_text, parse_edit_command


router = Router(name="planner")


class PlannerStates(StatesGroup):
    waiting_task_input = State()
    confirming_task = State()
    editing_title = State()
    waiting_voice_edit = State()


def _is_anton(event) -> bool:
    return event.from_user.id == settings.anton_chat_id


def _task_preview(task: dict) -> str:
    date_str = task.get("task_date") or "без даты"
    time_str = task.get("task_time") or "без времени"
    imp = " ⭐ ВАЖНАЯ" if task.get("is_important") else ""
    rec = f"\n🔁 Повтор: {task['recurring']}" if task.get("recurring") else ""
    return (
        f"📝 <b>{task['title']}</b>{imp}\n"
        f"📅 {date_str}  ⏰ {time_str}{rec}"
    )


def _format_tasks_text(tasks: list, overdue: list, title: str) -> str:
    if not tasks and not overdue:
        return f"{title}\n\nЗадач нет. ✅"
    lines = [title, ""]
    if overdue:
        lines.append("🔴 <b>Просроченные:</b>")
        for t in overdue[:5]:
            lines.append(f"  • [{t['task_date']}] {t['title']}")
        lines.append("")
    important = [t for t in tasks if t["is_important"]]
    regular_timed = sorted(
        [t for t in tasks if not t["is_important"] and t.get("task_time")],
        key=lambda x: x["task_time"],
    )
    untimed = [t for t in tasks if not t["is_important"] and not t.get("task_time")]
    if important:
        lines.append("⭐ <b>Важные:</b>")
        for t in sorted(important, key=lambda x: x.get("task_time") or "99:99"):
            tm = f"🕐 {t['task_time']} — " if t.get("task_time") else ""
            lines.append(f"  ⭐ {tm}{t['title']}")
        lines.append("")
    if regular_timed:
        lines.append("⏰ <b>По времени:</b>")
        for t in regular_timed:
            lines.append(f"  🕐 {t['task_time']} — {t['title']}")
        lines.append("")
    if untimed:
        lines.append("📌 <b>Без времени:</b>")
        for t in untimed:
            lines.append(f"  • {t['title']}")
    return "\n".join(lines)


# ── Planner menu ──────────────────────────────────────────────────────────────

@router.callback_query(F.data == "planner_menu")
async def planner_menu(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    await state.clear()
    today = datetime.now().strftime("%Y-%m-%d")
    tasks = await get_tasks_for_date(today)
    count = len(tasks)
    count_str = f" ({count} задач)" if count else ""
    await callback.message.edit_text(
        f"📅 <b>Планер</b>{count_str}\n\nЧто делаем?",
        reply_markup=planner_main_menu(),
    )
    await callback.answer()


# ── New task ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "planner_new")
async def planner_new_task(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    await callback.message.edit_text(
        "➕ <b>Новая задача</b>\n\n"
        "Скажи голосом или напиши текстом.\n\n"
        "Примеры:\n"
        "• <i>Встреча с поставщиком в пятницу в 15:00</i>\n"
        "• <i>Важно: позвонить Ивану завтра в 11</i>\n"
        "• <i>Оплатить аренду до конца недели</i>",
        reply_markup=back_to_main(),
    )
    await state.set_state(PlannerStates.waiting_task_input)
    await callback.answer()


@router.message(StateFilter(PlannerStates.waiting_task_input), F.text)
async def receive_task_text(message: Message, state: FSMContext) -> None:
    if not _is_anton(message):
        return
    await message.answer("⏳ Разбираю задачу...")
    parsed = await parse_task_from_text(message.text)
    await state.update_data(parsed_task=parsed)
    await state.set_state(PlannerStates.confirming_task)
    await message.answer(
        f"Проверь задачу:\n\n{_task_preview(parsed)}\n\nСохранить?",
        reply_markup=task_confirm_keyboard(),
    )


@router.message(StateFilter(PlannerStates.waiting_task_input), F.voice)
async def receive_task_voice(message: Message, state: FSMContext, bot: Bot) -> None:
    if not _is_anton(message):
        return
    await message.answer("🎙️ Расшифровываю...")
    voice_file = await bot.get_file(message.voice.file_id)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        await bot.download_file(voice_file.file_path, destination=str(tmp_path))
        from services.whisper_local import transcribe
        text = await transcribe(tmp_path)
    except Exception as e:
        logger.error(f"Planner voice transcription failed: {e}")
        await message.answer(f"⚠️ Ошибка расшифровки: {e}", reply_markup=planner_main_menu())
        await state.clear()
        return
    finally:
        tmp_path.unlink(missing_ok=True)

    if not text or len(text.strip()) < 3:
        await message.answer("⚠️ Не удалось расшифровать.", reply_markup=planner_main_menu())
        await state.clear()
        return

    await message.answer(f"📝 Расшифровал: <i>{text}</i>\n\n⏳ Разбираю...")
    parsed = await parse_task_from_text(text)
    await state.update_data(parsed_task=parsed)
    await state.set_state(PlannerStates.confirming_task)
    await message.answer(
        f"Проверь задачу:\n\n{_task_preview(parsed)}\n\nСохранить?",
        reply_markup=task_confirm_keyboard(),
    )


@router.callback_query(F.data == "planner_confirm_save")
async def confirm_save_task(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_anton(callback):
        return
    data = await state.get_data()
    parsed = data.get("parsed_task", {})
    if not parsed:
        await callback.message.edit_text("Данные потеряны. Начни заново.", reply_markup=planner_main_menu())
        await state.clear()
        return
    task_id = await add_task(
        title=parsed["title"],
        task_date=parsed.get("task_date"),
        task_time=parsed.get("task_time"),
        is_important=parsed.get("is_important", False),
        recurring=parsed.get("recurring"),
    )
    await state.clear()
    await callback.message.edit_text(
        f"✅ <b>Задача сохранена</b>\n\n{_task_preview(parsed)}",
        reply_markup=planner_main_menu(),
    )
    await callback.answer("Сохранено!")


@router.callback_query(F.data == "planner_confirm_edit")
async def confirm_edit_task(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_anton(callback):
        return
    await callback.message.edit_text(
        "✏️ Введи новое название задачи:",
        reply_markup=back_to_main(),
    )
    await state.set_state(PlannerStates.editing_title)
    await callback.answer()


@router.message(StateFilter(PlannerStates.editing_title), F.text)
async def receive_edited_title(message: Message, state: FSMContext) -> None:
    if not _is_anton(message):
        return
    data = await state.get_data()
    parsed = data.get("parsed_task", {})
    parsed["title"] = message.text.strip()
    await state.update_data(parsed_task=parsed)
    await state.set_state(PlannerStates.confirming_task)
    await message.answer(
        f"Проверь задачу:\n\n{_task_preview(parsed)}\n\nСохранить?",
        reply_markup=task_confirm_keyboard(),
    )


# ── Today / All tasks ─────────────────────────────────────────────────────────

@router.callback_query(F.data == "planner_today")
async def show_today_tasks(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    today = datetime.now().strftime("%Y-%m-%d")
    tasks = await get_tasks_for_date(today)
    overdue = await get_overdue_tasks(today)
    now_str = datetime.now().strftime("%d %B")
    text = _format_tasks_text(tasks, overdue, f"📋 <b>Задачи на сегодня ({now_str})</b>")
    await callback.message.edit_text(
        text,
        reply_markup=tasks_list_keyboard(tasks + overdue, back_cb="planner_menu"),
    )
    await callback.answer()


@router.callback_query(F.data == "planner_all")
async def show_all_tasks(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    tasks = await get_all_pending()
    if not tasks:
        await callback.message.edit_text(
            "📅 <b>Все задачи</b>\n\nЗадач нет.",
            reply_markup=planner_main_menu(),
        )
    else:
        await callback.message.edit_text(
            f"📅 <b>Все задачи</b> ({len(tasks)})\n\nВыбери задачу:",
            reply_markup=tasks_list_keyboard(tasks, back_cb="planner_menu"),
        )
    await callback.answer()


# ── Task detail ───────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("task_view:"))
async def task_view(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)
    if not task:
        await callback.answer("Задача не найдена.", show_alert=True)
        return
    await callback.message.edit_text(
        _task_preview(task),
        reply_markup=task_detail_keyboard(task_id, remind_1h=bool(task["remind_1h"])),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("task_done:"))
async def task_done(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        return
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)
    await mark_done(task_id)
    title = task["title"] if task else "Задача"
    await callback.message.edit_text(
        f"✅ Выполнено: <b>{title}</b>",
        reply_markup=planner_main_menu(),
    )
    await callback.answer("Отмечено!")


@router.callback_query(F.data.startswith("task_snooze:"))
async def task_snooze(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        return
    parts = callback.data.split(":")
    task_id = int(parts[1])
    minutes = int(parts[2])
    task = await get_task(task_id)
    if not task or not task.get("task_time"):
        await callback.answer("Нет времени для снуза.", show_alert=True)
        return
    t = datetime.strptime(task["task_time"], "%H:%M") + timedelta(minutes=minutes)
    new_time = t.strftime("%H:%M")
    await update_task(task_id, task_time=new_time, reminded_1h=0, reminded_at=0)
    await callback.message.edit_text(
        f"⏰ Перенесено на {new_time}: <b>{task['title']}</b>",
        reply_markup=planner_main_menu(),
    )
    await callback.answer(f"Снуз +{minutes} мин")


@router.callback_query(F.data.startswith("task_remind_off:"))
async def task_remind_off(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        return
    task_id = int(callback.data.split(":")[1])
    await update_task(task_id, remind_1h=0)
    task = await get_task(task_id)
    await callback.message.edit_text(
        f"🔕 Напоминание выключено\n\n{_task_preview(task)}",
        reply_markup=task_detail_keyboard(task_id, remind_1h=False),
    )
    await callback.answer("Напоминание выключено")


@router.callback_query(F.data.startswith("task_remind_on:"))
async def task_remind_on(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        return
    task_id = int(callback.data.split(":")[1])
    await update_task(task_id, remind_1h=1)
    task = await get_task(task_id)
    await callback.message.edit_text(
        f"🔔 Напоминание включено\n\n{_task_preview(task)}",
        reply_markup=task_detail_keyboard(task_id, remind_1h=True),
    )
    await callback.answer("Напоминание включено")


@router.callback_query(F.data.startswith("task_delete:"))
async def task_delete(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        return
    task_id = int(callback.data.split(":")[1])
    task = await get_task(task_id)
    await delete_task(task_id)
    title = task["title"] if task else "Задача"
    await callback.message.edit_text(
        f"🗑 Удалено: <b>{title}</b>",
        reply_markup=planner_main_menu(),
    )
    await callback.answer("Удалено")


# ── Voice edit ────────────────────────────────────────────────────────────────

@router.callback_query(F.data.startswith("task_voice_edit:"))
async def task_voice_edit_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_anton(callback):
        return
    task_id = int(callback.data.split(":")[1])
    await state.update_data(edit_task_id=task_id)
    await state.set_state(PlannerStates.waiting_voice_edit)
    task = await get_task(task_id)
    title = task["title"] if task else "задача"
    await callback.message.edit_text(
        f"🎙️ Скажи что изменить в задаче:\n<b>{title}</b>\n\n"
        "Примеры:\n"
        "• <i>Перенеси на завтра в 14:00</i>\n"
        "• <i>Переименуй в «Встреча с Иваном»</i>\n"
        "• <i>Удали задачу</i>",
        reply_markup=back_to_main(),
    )
    await callback.answer()


@router.message(StateFilter(PlannerStates.waiting_voice_edit), F.voice)
async def receive_voice_edit(message: Message, state: FSMContext, bot: Bot) -> None:
    if not _is_anton(message):
        return
    data = await state.get_data()
    task_id = data.get("edit_task_id")
    if not task_id:
        await message.answer("Нет задачи для редактирования.", reply_markup=planner_main_menu())
        await state.clear()
        return

    voice_file = await bot.get_file(message.voice.file_id)
    with tempfile.NamedTemporaryFile(suffix=".ogg", delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        await bot.download_file(voice_file.file_path, destination=str(tmp_path))
        from services.whisper_local import transcribe
        text = await transcribe(tmp_path)
    except Exception as e:
        await message.answer(f"⚠️ Ошибка расшифровки: {e}", reply_markup=planner_main_menu())
        await state.clear()
        return
    finally:
        tmp_path.unlink(missing_ok=True)

    await message.answer(f"🎙️ <i>{text}</i>\n\n⏳ Обрабатываю...")
    task = await get_task(task_id)
    if not task:
        await message.answer("Задача не найдена.", reply_markup=planner_main_menu())
        await state.clear()
        return

    edit = await parse_edit_command(text, task)
    if not edit:
        await message.answer("⚠️ Не понял команду. Попробуй ещё раз.", reply_markup=planner_main_menu())
        await state.clear()
        return

    action = edit.get("action", "none")
    if action == "delete":
        await delete_task(task_id)
        await message.answer(f"🗑 Задача удалена: <b>{task['title']}</b>", reply_markup=planner_main_menu())
    elif action == "done":
        await mark_done(task_id)
        await message.answer(f"✅ Выполнено: <b>{task['title']}</b>", reply_markup=planner_main_menu())
    elif action in ("reschedule", "rename"):
        updates = {}
        if edit.get("task_date"):
            updates["task_date"] = edit["task_date"]
        if edit.get("task_time"):
            updates["task_time"] = edit["task_time"]
            updates["reminded_1h"] = 0
            updates["reminded_at"] = 0
        if edit.get("title"):
            updates["title"] = edit["title"]
        if updates:
            await update_task(task_id, **updates)
        updated = await get_task(task_id)
        await message.answer(
            f"✅ Обновлено:\n\n{_task_preview(updated)}",
            reply_markup=planner_main_menu(),
        )
    else:
        await message.answer("⚠️ Команда не распознана.", reply_markup=planner_main_menu())

    await state.clear()


@router.message(StateFilter(PlannerStates.waiting_voice_edit), F.text)
async def receive_text_edit(message: Message, state: FSMContext) -> None:
    if not _is_anton(message):
        return
    data = await state.get_data()
    task_id = data.get("edit_task_id")
    if not task_id:
        await state.clear()
        return
    task = await get_task(task_id)
    edit = await parse_edit_command(message.text, task)
    if not edit:
        await message.answer("⚠️ Не понял.", reply_markup=planner_main_menu())
        await state.clear()
        return
    action = edit.get("action", "none")
    if action == "delete":
        await delete_task(task_id)
        await message.answer(f"🗑 Удалено: <b>{task['title']}</b>", reply_markup=planner_main_menu())
    elif action == "done":
        await mark_done(task_id)
        await message.answer(f"✅ Выполнено: <b>{task['title']}</b>", reply_markup=planner_main_menu())
    else:
        updates = {k: v for k, v in [
            ("task_date", edit.get("task_date")),
            ("task_time", edit.get("task_time")),
            ("title", edit.get("title")),
        ] if v}
        if updates:
            await update_task(task_id, **updates)
        updated = await get_task(task_id)
        await message.answer(f"✅ Обновлено:\n\n{_task_preview(updated)}", reply_markup=planner_main_menu())
    await state.clear()


# ── Settings ──────────────────────────────────────────────────────────────────

@router.callback_query(F.data == "planner_settings")
async def planner_settings(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        return
    notif = await get_setting("notifications_enabled", "1")
    enabled = notif == "1"
    status = "включены ✅" if enabled else "выключены 🔕"
    await callback.message.edit_text(
        f"⚙️ <b>Настройки планера</b>\n\nНапоминания: <b>{status}</b>",
        reply_markup=planner_settings_keyboard(enabled),
    )
    await callback.answer()


@router.callback_query(F.data == "planner_notif_off")
async def notif_off(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        return
    await set_setting("notifications_enabled", "0")
    await callback.message.edit_text(
        "⚙️ <b>Настройки планера</b>\n\nНапоминания: <b>выключены 🔕</b>",
        reply_markup=planner_settings_keyboard(False),
    )
    await callback.answer("Напоминания выключены")


@router.callback_query(F.data == "planner_notif_on")
async def notif_on(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        return
    await set_setting("notifications_enabled", "1")
    await callback.message.edit_text(
        "⚙️ <b>Настройки планера</b>\n\nНапоминания: <b>включены ✅</b>",
        reply_markup=planner_settings_keyboard(True),
    )
    await callback.answer("Напоминания включены")
