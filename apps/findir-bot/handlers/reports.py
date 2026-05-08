"""Сводка/отчёты из бота."""
from __future__ import annotations

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message

import api_client
from config import is_authorized, is_owner

router = Router()


def _fmt(n: float) -> str:
    return f"{n:,.0f}".replace(",", " ")


@router.message(Command("summary"))
@router.message(F.text == "📊 Сводка")
async def summary(message: Message):
    if not is_authorized(message.from_user.id):
        return
    try:
        s = await api_client.get_summary()
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
        return

    text = (
        f"📊 <b>Сводка · {s['period']} · {s['branch']}</b>\n\n"
        f"💵 Выручка: <b>{_fmt(s['revenue'])} ₽</b>\n"
        f"📦 Заказов: <b>{s['orders']}</b>\n"
        f"🧾 Ср. чек: <b>{_fmt(s['avg_check'])} ₽</b>\n"
        f"🥘 Food cost: <b>{s['food_cost_pct']:.1f}%</b>\n"
    )
    if is_owner(message.from_user.id):
        text += (
            f"\n👥 ФОТ: <b>{s['fot_pct']:.1f}%</b> выручки\n"
            f"💎 EBITDA: <b>{_fmt(s['ebitda'])} ₽</b> ({s['ebitda_pct']:.1f}%)\n"
            f"💰 Чистая прибыль: <b>{_fmt(s['net_profit'])} ₽</b> ({s['net_profit_pct']:.1f}%)\n"
        )
    text += "\nДашборд: https://findir.mistersushi36.pro"
    await message.answer(text)
