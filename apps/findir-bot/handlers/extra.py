"""
Ad-hoc расход за день — добавить любую статью с категорией и привязкой к филиалу.
Для еды персонала, разовых ремонтов и т.д.
"""
from __future__ import annotations

from datetime import date

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)

import api_client
from config import is_authorized

router = Router()

CATEGORIES = [
    ("staff_meals", "🍱 Еда персонала"),
    ("food_supply", "🥡 Поставки продуктов"),
    ("equipment", "🔧 Оборудование/ремонт"),
    ("communal_rent", "🏢 Коммуналка"),
    ("internet_phone", "📞 Интернет/телефон"),
    ("bank_commission", "💳 Банк. комиссия"),
    ("marketing_blogger", "🎬 Блогеры"),
    ("marketing_smm", "📱 SMM/таргет"),
    ("ya_eda", "🟡 Яндекс Еда"),
    ("kuper", "🟢 Купер"),
    ("ya_direct", "🔍 Яндекс Директ"),
    ("revvy", "⭐ REVVY"),
    ("site", "🌐 Сайт"),
    ("other", "📌 Прочее"),
]
BRANCHES = [(None, "Общий"), (1, "Ростовская"), (2, "9 Января")]


class ExtraForm(StatesGroup):
    branch = State()
    category = State()
    amount = State()
    note = State()


def branch_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"xbranch:{bid or 'none'}")
         for bid, name in BRANCHES]
    ])


def cat_kb() -> InlineKeyboardMarkup:
    rows = []
    for i in range(0, len(CATEGORIES), 2):
        chunk = CATEGORIES[i:i+2]
        rows.append([InlineKeyboardButton(text=label, callback_data=f"xcat:{key}")
                      for key, label in chunk])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def _num(text: str) -> float | None:
    try:
        return float(text.replace(",", ".").replace(" ", ""))
    except ValueError:
        return None


@router.message(Command("extra"))
@router.message(F.text == "➕ Доп. расход за день")
async def extra_start(message: Message, state: FSMContext):
    if not is_authorized(message.from_user.id):
        return
    await state.clear()
    await state.update_data(d=date.today().isoformat())
    await message.answer(
        f"📆 Дата: <b>{date.today().isoformat()}</b>\n"
        f"Выбери филиал:",
        reply_markup=branch_kb(),
    )
    await state.set_state(ExtraForm.branch)


@router.callback_query(F.data.startswith("xbranch:"), ExtraForm.branch)
async def cb_xbranch(cb: CallbackQuery, state: FSMContext):
    raw = cb.data.split(":")[1]
    bid = None if raw == "none" else int(raw)
    name = dict(BRANCHES)[bid]
    await state.update_data(branch_id=bid, branch_name=name)
    await cb.message.edit_text(
        f"🏪 {name}\n\n📋 Выбери категорию расхода:",
        reply_markup=cat_kb(),
    )
    await state.set_state(ExtraForm.category)


@router.callback_query(F.data.startswith("xcat:"), ExtraForm.category)
async def cb_xcat(cb: CallbackQuery, state: FSMContext):
    cat = cb.data.split(":")[1]
    label = dict(CATEGORIES).get(cat, cat)
    await state.update_data(category=cat, cat_label=label)
    await cb.message.edit_text(f"📋 {label}\n\n💰 Введи сумму ₽:")
    await state.set_state(ExtraForm.amount)


@router.message(ExtraForm.amount)
async def st_amount(message: Message, state: FSMContext):
    v = _num(message.text)
    if v is None:
        await message.answer("⚠️ Введи число")
        return
    await state.update_data(amount=v)
    await message.answer("📝 Заметка (или - чтобы пропустить):")
    await state.set_state(ExtraForm.note)


@router.message(ExtraForm.note)
async def st_note(message: Message, state: FSMContext):
    note = None if message.text.strip() == "-" else message.text.strip()
    data = await state.get_data()
    try:
        await api_client.post_daily_extra(
            date=data["d"], branch_id=data.get("branch_id"),
            category=data["category"], amount=data["amount"],
            tg_user_id=message.from_user.id, note=note,
        )
        await message.answer(
            f"✅ Сохранено\n\n"
            f"📆 {data['d']} · 🏪 {data['branch_name']}\n"
            f"📋 {data['cat_label']}\n"
            f"💰 <b>{data['amount']:,.0f} ₽</b>\n\n"
            f"📊 https://findir.mistersushi36.pro/history?kind=extra".replace(",", " "),
        )
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()
