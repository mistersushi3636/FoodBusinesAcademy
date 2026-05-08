"""Месячный расход (только владелец)."""
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)

import api_client
from config import is_owner

router = Router()

CATEGORIES = [
    ("food_supply", "🥡 Поставки продуктов"),
    ("communal_rent", "🏢 Коммуналка + аренда + охрана"),
    ("internet_phone", "📞 Интернет + телефон"),
    ("equipment", "🔧 Оборудование/ремонт"),
    ("bank_credit", "🏦 Кредиты/займы"),
    ("bank_commission", "💳 Банк. комиссии"),
    ("marketing_blogger", "🎬 Блогеры/партнёрства"),
    ("marketing_smm", "📱 SMM/таргет"),
    ("ya_eda", "🟡 Яндекс Еда"),
    ("kuper", "🟢 Купер"),
    ("ya_direct", "🔍 Яндекс Директ"),
    ("revvy", "⭐ REVVY"),
    ("site", "🌐 Сайт (goulash.tech)"),
    ("taxes", "🧾 Налоги (АУСН 8%)"),
    ("other", "📌 Прочее"),
]

BRANCHES = [(None, "Общие"), (1, "Ростовская"), (2, "9 Января")]


class MonthlyForm(StatesGroup):
    branch = State()
    category = State()
    amount = State()
    note = State()


def cat_kb() -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(CATEGORIES), 2):
        chunk = CATEGORIES[i:i+2]
        rows.append([InlineKeyboardButton(text=label, callback_data=f"mcat:{key}")
                      for key, label in chunk])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def branch_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"mbranch:{bid or 'none'}")
         for bid, name in BRANCHES]
    ])


def _num(text: str) -> float | None:
    try:
        return float(text.replace(",", ".").replace(" ", ""))
    except ValueError:
        return None


def _period_now() -> str:
    from datetime import date
    return date.today().strftime("%Y-%m")


@router.message(Command("monthly"))
@router.message(F.text == "📅 Месячный расход")
async def monthly_start(message: Message, state: FSMContext):
    if not is_owner(message.from_user.id):
        await message.answer("🚫 Только владелец может вносить месячные расходы")
        return
    await state.clear()
    await state.update_data(period=_period_now())
    await message.answer(
        f"📅 Период: <b>{_period_now()}</b>\n"
        f"Выбери филиал:",
        reply_markup=branch_kb(),
    )
    await state.set_state(MonthlyForm.branch)


@router.callback_query(F.data.startswith("mbranch:"), MonthlyForm.branch)
async def cb_mbranch(cb: CallbackQuery, state: FSMContext):
    bid_raw = cb.data.split(":")[1]
    bid = None if bid_raw == "none" else int(bid_raw)
    name = dict(BRANCHES)[bid]
    await state.update_data(branch_id=bid, branch_name=name)
    await cb.message.edit_text(
        f"🏪 {name}\n\n📋 Выбери категорию расхода:",
        reply_markup=cat_kb(),
    )
    await state.set_state(MonthlyForm.category)


@router.callback_query(F.data.startswith("mcat:"), MonthlyForm.category)
async def cb_mcat(cb: CallbackQuery, state: FSMContext):
    cat = cb.data.split(":")[1]
    label = dict(CATEGORIES).get(cat, cat)
    await state.update_data(category=cat, cat_label=label)
    await cb.message.edit_text(f"📋 {label}\n\n💰 Введи сумму ₽:")
    await state.set_state(MonthlyForm.amount)


@router.message(MonthlyForm.amount)
async def st_amount(message: Message, state: FSMContext):
    v = _num(message.text)
    if v is None:
        await message.answer("⚠️ Введи число")
        return
    await state.update_data(amount=v)
    await message.answer("📝 Заметка (или - чтобы пропустить):")
    await state.set_state(MonthlyForm.note)


@router.message(MonthlyForm.note)
async def st_note(message: Message, state: FSMContext):
    note = None if message.text.strip() == "-" else message.text.strip()
    data = await state.get_data()
    try:
        await api_client.post_monthly(
            period=data["period"], category=data["category"],
            amount=data["amount"], tg_user_id=message.from_user.id,
            branch_id=data.get("branch_id"), note=note,
        )
        await message.answer(
            f"✅ Сохранено\n\n"
            f"📅 {data['period']} · 🏪 {data['branch_name']}\n"
            f"📋 {data['cat_label']}\n"
            f"💰 <b>{data['amount']:,.0f} ₽</b>".replace(",", " "),
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()
