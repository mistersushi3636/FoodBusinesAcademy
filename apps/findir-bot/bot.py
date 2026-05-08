"""Финдир-бот MR.SUSHI: aiogram polling."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from loguru import logger

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent / ".env")
    load_dotenv(Path(__file__).parents[2] / ".env")
except ImportError:
    pass

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

from config import settings
from handlers import (start as h_start, daily as h_daily,
                       extra as h_extra, monthly as h_monthly, reports as h_reports)


async def main() -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/findir_{time}.log", rotation="5 MB", retention="14 days")

    if not settings.bot_token:
        logger.error("FINDIR_BOT_TOKEN не задан в .env")
        sys.exit(1)
    if not settings.dashboard_api_key:
        logger.error("DASHBOARD_API_KEY не задан в .env")
        sys.exit(1)

    bot = Bot(token=settings.bot_token,
              default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(h_start.router)
    dp.include_router(h_daily.router)
    dp.include_router(h_extra.router)
    dp.include_router(h_monthly.router)
    dp.include_router(h_reports.router)

    logger.info(f"Findir bot starting. Dashboard: {settings.dashboard_api_url}")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Findir bot stopped.")
