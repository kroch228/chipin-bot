from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="groups")


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📖 <b>Команды Chipin:</b>\n\n"
        "/add <i>сумма описание @участники</i> — добавить расход\n"
        "/balance — текущие балансы группы\n"
        "/settle — кто кому должен (оптимально)\n"
        "/close — закрыть период расчётов\n"
        "/help — эта справка\n\n"
        "Бот работает только в групповых чатах. "
        "Добавьте бота в группу и дайте права на чтение сообщений."
    )
