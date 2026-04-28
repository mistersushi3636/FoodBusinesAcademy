import asyncio
import sys
from pathlib import Path

# Add vault root to path so `apps.shared` imports work
sys.path.insert(0, str(Path(__file__).parents[2]))

from loguru import logger
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from config import settings
from handlers import voice, chat, metrics

_start_router = Router(name="start")


def _is_anton(event) -> bool:
    return event.from_user.id == settings.anton_chat_id


@_start_router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not _is_anton(message):
        await message.answer("Бот персональный, доступ только владельцу.")
        return
    await message.answer(
        "👋 Антон, привет.\n\n"
        "Отправь <b>голосовое</b> — расшифрую и запущу пайплайн.\n"
        "Отправь <b>текст</b> — отвечу как ассистент.\n\n"
        "Команды:\n"
        "/clear — очистить историю диалога\n"
        "/start — это меню"
    )


@_start_router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "👋 Отправь голосовое или текст — я на связи."
    )
    await callback.answer()


async def main() -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level)
    Path("logs").mkdir(exist_ok=True)
    logger.add("logs/bot_{time}.log", rotation="10 MB", retention="30 days", level="DEBUG")

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    import orchestrator
    orchestrator.setup()

    dp.include_router(_start_router)
    dp.include_router(metrics.router)  # before chat — detects filled metrics forms
    dp.include_router(voice.router)
    dp.include_router(chat.router)     # fallback — must be last

    logger.info(f"FBA Assistant V3 starting. Vault: {settings.vault_path}")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
