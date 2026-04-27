import asyncio
import sys
from loguru import logger

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from handlers import start, ideas, metrics, voice, plans, notifications, planner, humanizer, chat


async def main() -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
    logger.add("logs/bot_{time}.log", rotation="10 MB", retention="30 days", level="DEBUG")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    from services.planner_db import init_db
    from services.task_scheduler import setup_task_scheduler
    await init_db()

    dp.include_router(start.router)
    dp.include_router(planner.router)   # before voice — handles voice in planner states
    dp.include_router(ideas.router)
    dp.include_router(metrics.router)
    dp.include_router(plans.router)
    dp.include_router(voice.router)
    dp.include_router(notifications.router)
    dp.include_router(humanizer.router)
    dp.include_router(chat.router)   # fallback — must be last

    notifications.setup_notification_listener(bot)
    setup_task_scheduler(bot)

    logger.info(f"Bot starting. Vault: {settings.vault_path}. Whisper: {settings.whisper_model}")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
