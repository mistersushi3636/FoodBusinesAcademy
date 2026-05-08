"""
Ввод данных за день (без staff_meals — он теперь через ad-hoc /extra).
Флоу:
1) дата (по умолчанию сегодня)
2) филиал
3) выручка доставка ₽
4) выручка самовывоз ₽
5) заказов доставка
6) заказов самовывоз
7) покупки магазин ₽
8) хоз/тара/упаковка ₽
9) подтверждение → POST /api/daily
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

BRANCHES = [(1, "Ростовская"), (2, "9 Января")]


class DailyForm(StatesGroup):
    branch = State()
    rev_del = State()
    rev_pick = State()
    ord_del = State()
    ord_pick = State()
    shop = State()
    household = State()
    confirm = State()


def branch_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=name, callback_data=f"daily_branch:{bid}")
         for bid, name in BRANCHES]
    ])


def confirm_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="✅ Сохранить", callback_data="daily_save"),
        InlineKeyboardButton(text="❌ Отмена", callback_data="daily_cancel"),
    ]])


def _num(text: str) -> float | None:
    try:
        return float(text.replace(",", ".").replace(" ", ""))
    except ValueError:
        return None


def _int(text: str) -> int | None:
    try:
        return int(text.replace(" ", ""))
    except ValueError:
        return None


@router.message(Command("daily"))
@router.message(F.text == "💰 Внести выручку")
@router.message(F.text == "🛒 Расходы за день")
async def daily_start(message: Message, state: FSMContext):
    if not is_authorized(message.from_user.id):
        return
    await state.clear()
    await state.update_data(d=date.today().isoformat())
    await message.answer(
        f"📆 Дата: <b>{date.today().isoformat()}</b>\n"
        f"Выбери филиал:",
        reply_markup=branch_kb(),
    )
    await state.set_state(DailyForm.branch)


@router.callback_query(F.data.startswith("daily_branch:"), DailyForm.branch)
async def cb_branch(cb: CallbackQuery, state: FSMContext):
    bid = int(cb.data.split(":")[1])
    name = dict(BRANCHES)[bid]
    await state.update_data(branch_id=bid, branch_name=name)
    await cb.message.edit_text(f"🏪 Филиал: <b>{name}</b>\n\n💵 Выручка <b>доставка</b> в ₽:")
    await state.set_state(DailyForm.rev_del)


@router.message(DailyForm.rev_del)
async def st_rev_del(message: Message, state: FSMContext):
    v = _num(message.text)
    if v is None:
        await message.answer("⚠️ Введи число")
        return
    await state.update_data(rev_del=v)
    await message.answer("💵 Выручка <b>самовывоз</b> в ₽:")
    await state.set_state(DailyForm.rev_pick)


@router.message(DailyForm.rev_pick)
async def st_rev_pick(message: Message, state: FSMContext):
    v = _num(message.text)
    if v is None:
        await message.answer("⚠️ Введи число")
        return
    await state.update_data(rev_pick=v)
    await message.answer("📦 Заказов <b>доставка</b>:")
    await state.set_state(DailyForm.ord_del)


@router.message(DailyForm.ord_del)
async def st_ord_del(message: Message, state: FSMContext):
    v = _int(message.text)
    if v is None:
        await message.answer("⚠️ Введи целое число")
        return
    await state.update_data(ord_del=v)
    await message.answer("🛍 Заказов <b>самовывоз</b>:")
    await state.set_state(DailyForm.ord_pick)


@router.message(DailyForm.ord_pick)
async def st_ord_pick(message: Message, state: FSMContext):
    v = _int(message.text)
    if v is None:
        await message.answer("⚠️ Введи целое число")
        return
    await state.update_data(ord_pick=v)
    await message.answer("🛒 Покупки магазин (продукты) ₽\nЕсли не было — 0:")
    await state.set_state(DailyForm.shop)


@router.message(DailyForm.shop)
async def st_shop(message: Message, state: FSMContext):
    v = _num(message.text)
    if v is None:
        await message.answer("⚠️ Введи число")
        return
    await state.update_data(shop=v)
    await message.answer("📦 Хоз. средства, тара, упаковка ₽ (0 если не было):")
    await state.set_state(DailyForm.household)


@router.message(DailyForm.household)
async def st_household(message: Message, state: FSMContext):
    v = _num(message.text)
    if v is None:
        await message.answer("⚠️ Введи число")
        return
    await state.update_data(household=v)
    data = await state.get_data()
    rev_total = data["rev_del"] + data["rev_pick"]
    ord_total = data["ord_del"] + data["ord_pick"]
    avg = rev_total / ord_total if ord_total else 0
    summary = (
        f"📋 <b>Проверь данные</b>\n\n"
        f"📆 {data['d']} · 🏪 {data['branch_name']}\n\n"
        f"💵 Выручка:\n"
        f"  Доставка: {data['rev_del']:,.0f} ₽\n"
        f"  Самовывоз: {data['rev_pick']:,.0f} ₽\n"
        f"  Всего: <b>{rev_total:,.0f} ₽</b>\n\n"
        f"📦 Заказов:\n"
        f"  Доставка: {data['ord_del']}\n"
        f"  Самовывоз: {data['ord_pick']}\n"
        f"  Всего: <b>{ord_total}</b>\n"
        f"  Ср. чек: <b>{avg:,.0f} ₽</b>\n\n"
        f"💸 Расходы:\n"
        f"  Магазин: {data['shop']:,.0f} ₽\n"
        f"  Хоз/тара: {data['household']:,.0f} ₽\n\n"
        f"💡 Доп. расходы (еда персонала, разовые) — через /extra"
    ).replace(",", " ")
    await message.answer(summary, reply_markup=confirm_kb())
    await state.set_state(DailyForm.confirm)


@router.callback_query(F.data == "daily_save", DailyForm.confirm)
async def cb_save(cb: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    try:
        await api_client.post_daily(
            date=data["d"], branch_id=data["branch_id"], tg_user_id=cb.from_user.id,
            revenue_delivery=data["rev_del"], revenue_pickup=data["rev_pick"],
            orders_delivery=data["ord_del"], orders_pickup=data["ord_pick"],
            shop_purchase=data["shop"], household=data["household"],
        )
        await cb.message.edit_text(
            f"✅ Сохранено!\n\n"
            f"📊 Дашборд: https://findir.mistersushi36.pro"
        )
    except Exception as e:
        await cb.message.edit_text(f"❌ Ошибка: {e}\nПопробуй ещё раз: /daily")
    await state.clear()


@router.callback_query(F.data == "daily_cancel")
async def cb_cancel(cb: CallbackQuery, state: FSMContext):
    await state.clear()
    await cb.message.edit_text("❌ Отменено")
