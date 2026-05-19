import asyncio
import logging
import sys

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from core.config import settings
from core.database import engine


def setup_logging() -> None:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.StackInfoRenderer(),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.getLevelName(settings.log_level)
        ),
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )


async def on_shutdown(dp: Dispatcher) -> None:
    await engine.dispose()


async def main() -> None:
    setup_logging()
    log = structlog.get_logger()

    if not settings.bot_token:
        log.error("BOT_TOKEN is not set")
        sys.exit(1)

    from bot.handlers import router
    from bot.health import start_health_server

    bot = Bot(token=settings.bot_token, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher()
    dp.include_router(router)
    dp.shutdown.register(on_shutdown)

    health_runner = await start_health_server()
    log.info("Bot starting", log_level=settings.log_level)

    try:
        await dp.start_polling(bot)
    finally:
        await health_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
