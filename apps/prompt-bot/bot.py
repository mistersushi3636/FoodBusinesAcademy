"""FBA Prompt Bot — выдаёт готовые промпты ChatGPT Image."""
import asyncio
import sys
from pathlib import Path

# vault root for `apps.shared.*` imports
sys.path.insert(0, str(Path(__file__).parents[2]))

from loguru import logger
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings
from handlers import prompts


async def main() -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/prompt_bot_{time}.log", rotation="5 MB", retention="14 days")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(prompts.router)

    logger.info(f"FBA Prompt Bot starting. Anton: {settings.anton_chat_id}")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("FBA Prompt Bot stopped.")
