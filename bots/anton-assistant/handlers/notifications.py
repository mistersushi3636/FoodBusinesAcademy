"""Notifications from cron / Claude Code → bot.

Claude Code drops messages into VAULT/bots/anton-assistant/inbox/ as JSON files.
A background watcher picks them up and sends via bot to Anton.

JSON format:
{
  "type": "plan_ready" | "metrics_reminder" | "general",
  "text": "message body",
  "buttons": [{"text": "ОК", "callback_data": "plan_ok"}]  # optional
}
"""

import asyncio
import json
from pathlib import Path

from aiogram import Bot, Router, F
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder
from loguru import logger

from config import settings


router = Router(name="notifications")


INBOX_DIR = settings.vault_path / "bots" / "anton-assistant" / "inbox"
PROCESSED_DIR = settings.vault_path / "bots" / "anton-assistant" / "inbox" / ".processed"


@router.callback_query(F.data.startswith("plan_ok"))
async def plan_acknowledged(callback: CallbackQuery) -> None:
    if callback.from_user.id != settings.anton_chat_id:
        return
    await callback.message.edit_text(callback.message.text + "\n\n✅ Принято. Передаю в calendar.")
    flag = settings.vault_path / "content" / "plans" / ".latest-approved"
    flag.parent.mkdir(parents=True, exist_ok=True)
    flag.write_text("approved", encoding="utf-8")
    await callback.answer("Передал.")


@router.callback_query(F.data.startswith("plan_revise"))
async def plan_revise(callback: CallbackQuery) -> None:
    if callback.from_user.id != settings.anton_chat_id:
        return
    await callback.message.answer(
        "✏️ Напиши какие правки нужны. Я передам в content-marketer.",
    )
    await callback.answer()


async def _watch_inbox(bot: Bot) -> None:
    INBOX_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    while True:
        try:
            for file in INBOX_DIR.glob("*.json"):
                if file.parent != INBOX_DIR:
                    continue
                try:
                    data = json.loads(file.read_text(encoding="utf-8"))
                except Exception as e:
                    logger.error(f"Bad notification JSON {file.name}: {e}")
                    file.rename(PROCESSED_DIR / f"failed-{file.name}")
                    continue

                text = data.get("text", "")
                buttons = data.get("buttons", [])
                ntype = data.get("type", "general")

                if buttons:
                    builder = InlineKeyboardBuilder()
                    for btn in buttons:
                        builder.row(
                            InlineKeyboardButton(
                                text=btn["text"], callback_data=btn["callback_data"]
                            )
                        )
                    keyboard = builder.as_markup()
                else:
                    keyboard = None

                try:
                    await bot.send_message(
                        chat_id=settings.anton_chat_id,
                        text=text[:4000],
                        reply_markup=keyboard,
                    )
                    file.rename(PROCESSED_DIR / file.name)
                    logger.info(f"Sent notification ({ntype}): {file.name}")
                except Exception as e:
                    logger.error(f"Failed to send notification: {e}")
        except Exception as e:
            logger.error(f"Inbox watcher error: {e}")

        await asyncio.sleep(5)


def setup_notification_listener(bot: Bot) -> None:
    """Call once during bot startup to launch background inbox watcher."""
    asyncio.create_task(_watch_inbox(bot))
    logger.info(f"Notification watcher started (inbox: {INBOX_DIR})")
