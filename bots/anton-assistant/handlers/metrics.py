from datetime import datetime

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from config import settings
from keyboards.main_menu import main_menu, back_to_main
from services.vault_writer import save_metrics_entry


router = Router(name="metrics")


class MetricsStates(StatesGroup):
    waiting_input = State()


def _is_anton(event) -> bool:
    return event.from_user.id == settings.anton_chat_id


def _current_week_id() -> str:
    today = datetime.now()
    iso_year, iso_week, _ = today.isocalendar()
    return f"{iso_year}-W{iso_week:02d}"


@router.callback_query(F.data == "enter_metrics")
async def enter_metrics_prompt(callback: CallbackQuery, state: FSMContext) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return
    week_id = _current_week_id()
    text = (
        f"📊 <b>Метрики недели {week_id}</b>\n\n"
        "Пришли цифры в свободной форме. Например:\n\n"
        "<i>TG пост про маржу: 1247 views, 38 likes, 4 шера, +6 подписчиков\n"
        "TikTok ролик доставка: 8500, 320 likes, 67 saves\n"
        "...</i>\n\n"
        "Или просто список постов и метрик. Я сохраню как есть, агент потом разберёт."
    )
    await callback.message.edit_text(text, reply_markup=back_to_main())
    await state.set_state(MetricsStates.waiting_input)
    await state.update_data(week_id=week_id)
    await callback.answer()


@router.message(StateFilter(MetricsStates.waiting_input), F.text)
async def receive_metrics(message: Message, state: FSMContext) -> None:
    if not _is_anton(message):
        return
    data = await state.get_data()
    week_id = data.get("week_id", _current_week_id())
    path = await save_metrics_entry(week_id, message.text)
    await state.clear()
    await message.answer(
        f"✅ Метрики записаны: <code>{path.name}</code>\n\n"
        "В понедельник 11:00 cron запустит /content-planner — проанализирует и составит новый план.",
        reply_markup=main_menu(),
    )
