"""
Telegram publisher: auto-post to FBA channel + send semi-auto drafts for IG/YT.
Uses Bot API directly (not aiogram) for fire-and-forget publishing.
"""
from pathlib import Path

import httpx
from loguru import logger

TG_API = "https://api.telegram.org/bot{token}/{method}"


async def post_to_channel(
    *,
    bot_token: str,
    channel_id: str,
    text: str,
    image_path: Path | None = None,
    parse_mode: str = "HTML",
) -> dict:
    """
    Auto-post text (+ optional image) to TG channel.
    channel_id: "@Food_Busines_Academy" or numeric -100...
    Returns Bot API response dict.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        if image_path and image_path.exists():
            url = TG_API.format(token=bot_token, method="sendPhoto")
            with open(image_path, "rb") as img:
                resp = await client.post(url, data={
                    "chat_id": channel_id,
                    "caption": text,
                    "parse_mode": parse_mode,
                }, files={"photo": img})
        else:
            url = TG_API.format(token=bot_token, method="sendMessage")
            resp = await client.post(url, json={
                "chat_id": channel_id,
                "text": text,
                "parse_mode": parse_mode,
                "disable_web_page_preview": True,
            })

    data = resp.json()
    if not data.get("ok"):
        logger.error(f"TG publish failed: {data}")
    else:
        logger.info(f"Published to {channel_id}: msg_id={data['result']['message_id']}")
    return data


async def send_semi_auto_draft(
    *,
    bot_token: str,
    anton_chat_id: int,
    platform: str,
    draft_text: str,
    image_path: Path | None = None,
    task_id: int | None = None,
    extra_instructions: str = "",
) -> None:
    """
    Send IG or YT draft to Anton's personal chat for manual publishing.
    Includes inline buttons to confirm or cancel task.
    """
    platform_icons = {"instagram": "📸", "youtube": "📺", "tiktok": "🎵"}
    icon = platform_icons.get(platform, "📱")

    header = (
        f"{icon} <b>{platform.upper()} draft готов</b>\n"
        f"{'─' * 30}\n\n"
    )
    footer = f"\n\n{'─' * 30}\n{extra_instructions}" if extra_instructions else ""

    message = header + draft_text + footer

    if len(message) > 4096:
        message = message[:4050] + "\n\n[...обрезано]"

    async with httpx.AsyncClient(timeout=30) as client:
        payload: dict = {
            "chat_id": anton_chat_id,
            "text": message,
            "parse_mode": "HTML",
        }

        # Inline keyboard for task tracking
        if task_id:
            payload["reply_markup"] = {
                "inline_keyboard": [[
                    {"text": "✅ Опубликовал", "callback_data": f"done:{task_id}:{platform}"},
                    {"text": "❌ Отмена",      "callback_data": f"cancel:{task_id}:{platform}"},
                ]]
            }

        url = TG_API.format(token=bot_token, method="sendMessage")
        resp = await client.post(url, json=payload)
        data = resp.json()

        if not data.get("ok"):
            logger.error(f"semi-auto send failed: {data}")
        else:
            logger.info(f"Semi-auto draft sent to Anton: task={task_id} platform={platform}")

        # Send image separately if exists
        if image_path and image_path.exists():
            with open(image_path, "rb") as img:
                img_url = TG_API.format(token=bot_token, method="sendPhoto")
                await client.post(img_url, data={"chat_id": anton_chat_id}, files={"photo": img})
