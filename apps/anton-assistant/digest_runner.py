"""Утренний дайджест 9:00. Шлёт Антону через @AntonFBAbot список карточек на утверждение, дедлайны и идеи."""
import asyncio
import sqlite3
import sys
from datetime import date, timedelta
from pathlib import Path

# vault root for shared imports
sys.path.insert(0, str(Path(__file__).parents[2]))

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from loguru import logger

from config import settings

FBA_DB = settings.vault_path / "apps" / "dashboard" / "projects" / "fba-2-0.db"
DASH_URL = "https://mistersushi36.pro/p/fba-2-0/content"

PLATFORM_LBL = {"telegram": "TG", "instagram": "IG", "youtube": "YT", "cross": "✕"}
FORMAT_LBL = {"post": "пост", "carousel": "карусель", "reels": "Reels", "longvideo": "длинное", "story": "сторис"}


def _query() -> dict:
    if not FBA_DB.exists():
        return {"pending": [], "soon": [], "in_work": [], "ideas_new": 0}
    conn = sqlite3.connect(str(FBA_DB))
    conn.row_factory = sqlite3.Row

    pending = conn.execute(
        "SELECT id, platform, format_type, topic, scheduled_date "
        "FROM content_plan WHERE status='pending' "
        "ORDER BY scheduled_date IS NULL, scheduled_date LIMIT 12"
    ).fetchall()

    today = date.today()
    in_3 = (today + timedelta(days=3)).strftime("%Y-%m-%d")
    today_s = today.strftime("%Y-%m-%d")

    soon = conn.execute(
        "SELECT id, platform, format_type, topic, scheduled_date "
        "FROM content_plan WHERE status='approved' "
        "AND scheduled_date BETWEEN ? AND ? "
        "ORDER BY scheduled_date LIMIT 10",
        (today_s, in_3),
    ).fetchall()

    in_work = conn.execute(
        "SELECT id, platform, format_type, topic, scheduled_date, status "
        "FROM content_plan WHERE status IN ('production','ready') "
        "ORDER BY scheduled_date LIMIT 10"
    ).fetchall()

    ideas_new = conn.execute("SELECT COUNT(*) FROM ideas WHERE status='new'").fetchone()[0]

    conn.close()
    return {
        "pending": [dict(r) for r in pending],
        "soon": [dict(r) for r in soon],
        "in_work": [dict(r) for r in in_work],
        "ideas_new": ideas_new,
    }


def _fmt_card(c: dict) -> str:
    plt = PLATFORM_LBL.get(c["platform"], c["platform"])
    fmt = FORMAT_LBL.get(c["format_type"], c["format_type"])
    d = c.get("scheduled_date") or "—"
    return f"  • <a href=\"{DASH_URL}/{c['id']}\">#{c['id']}</a> {d} · {plt}/{fmt} · {c['topic'][:55]}"


def _build_message(data: dict) -> str:
    today_ru = date.today().strftime("%d.%m.%Y")
    parts = [f"☀️ <b>Доброе утро, Антон.</b>\n📅 {today_ru}\n"]

    pending = data["pending"]
    if pending:
        parts.append(f"\n📋 <b>На утверждение ({len(pending)}):</b>")
        parts += [_fmt_card(c) for c in pending]
    else:
        parts.append("\n✅ Всё утверждено.")

    soon = data["soon"]
    if soon:
        parts.append(f"\n\n⚡️ <b>Дедлайн ≤3 дней ({len(soon)}):</b>")
        parts += [_fmt_card(c) for c in soon]

    in_work = data["in_work"]
    if in_work:
        parts.append(f"\n\n🎬 <b>В работе ({len(in_work)}):</b>")
        parts += [_fmt_card(c) for c in in_work]

    if data["ideas_new"]:
        parts.append(f"\n\n💡 Новых идей в ящике: <b>{data['ideas_new']}</b>")

    parts.append(f"\n\n<a href=\"{DASH_URL}\">Открыть контент-план →</a>")
    return "\n".join(parts)


async def main() -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)

    data = _query()
    if not (data["pending"] or data["soon"] or data["in_work"] or data["ideas_new"]):
        logger.info("Digest: nothing to report — skip.")
        return

    body = _build_message(data)
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="📋 Открыть план", url=DASH_URL),
    ]])

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    try:
        await bot.send_message(
            settings.anton_chat_id, body[:4000],
            reply_markup=kb,
            disable_web_page_preview=True,
        )
        logger.info("Morning digest sent.")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
