from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

from core.database import async_session
from core.repositories import UserRepo

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    if not message.from_user:
        return

    async with async_session() as session:
        repo = UserRepo(session)
        await repo.get_or_create(
            user_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )
        await session.commit()

    await message.answer(
        "👋 Привет! Я <b>Chipin</b> — бот для разделения расходов в группах.\n\n"
        "Добавь меня в групповой чат и используй:\n"
        "/add <i>сумма описание @участники</i> — добавить расход\n"
        "/balance — текущие балансы\n"
        "/settle — кто кому должен\n"
        "/close — закрыть период\n"
        "/help — справка"
    )


@router.message(CommandStart(), flags={"chat_type": "group"})
async def cmd_start_group(message: Message) -> None:
    await message.answer(
        "👋 <b>Chipin</b> активирован в этой группе!\nИспользуйте /help для списка команд."
    )
