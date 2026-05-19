from aiogram import Router
from aiogram.types import Message

from bot.handlers.expenses import router as expenses_router
from bot.handlers.groups import router as groups_router
from bot.handlers.start import router as start_router

router = Router(name="main")
router.include_router(start_router)
router.include_router(expenses_router)
router.include_router(groups_router)


@router.errors()
async def error_handler(event, exception: Exception) -> bool:
    import structlog

    log = structlog.get_logger()
    log.error("Unhandled error in handler", exc_info=exception)
    if hasattr(event, "update") and event.update.message:
        msg: Message = event.update.message
        await msg.answer("⚠️ Произошла ошибка. Попробуйте позже.")
    return True
