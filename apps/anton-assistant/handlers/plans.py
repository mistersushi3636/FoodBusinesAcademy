from aiogram import Router, F
from aiogram.types import CallbackQuery

from config import settings, PLANS_DIR
from keyboards.main_menu import main_menu, back_to_main
from utils.markdown import read_markdown


router = Router(name="plans")


def _is_anton(event) -> bool:
    return event.from_user.id == settings.anton_chat_id


@router.callback_query(F.data == "content_plan")
async def show_content_plan(callback: CallbackQuery) -> None:
    if not _is_anton(callback):
        await callback.answer("Доступ закрыт.", show_alert=True)
        return

    if not PLANS_DIR.exists():
        await callback.message.edit_text(
            "📅 Планов пока нет.\nПервый сгенерится в понедельник 11:00 (cron → /content-planner).",
            reply_markup=back_to_main(),
        )
        await callback.answer()
        return

    plan_files = sorted(
        [p for p in PLANS_DIR.glob("*.md") if not p.name.startswith("README")],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    if not plan_files:
        await callback.message.edit_text(
            "📅 Планов пока нет.\nПервый сгенерится в понедельник 11:00.",
            reply_markup=back_to_main(),
        )
        await callback.answer()
        return

    latest = plan_files[0]
    metadata, content = await read_markdown(latest)
    status = metadata.get("status", "?")
    week = metadata.get("cycle_week", latest.stem)
    preview = content[:3000]

    text = (
        f"📅 <b>Текущий план</b>\n"
        f"Неделя: <b>{week}</b>\n"
        f"Статус: <b>{status}</b>\n\n"
        f"{preview}{'…' if len(content) > 3000 else ''}"
    )
    await callback.message.edit_text(text, reply_markup=main_menu())
    await callback.answer()
