import asyncio
import sys
from loguru import logger

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from handlers import start


async def main() -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
    logger.add("logs/leadmagnet_{time}.log", rotation="5 MB", retention="14 days")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(start.router)

    logger.info(f"Lead-magnet bot starting. Channel: {settings.channel_id}")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Lead-magnet bot stopped.")
