from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from core.database import async_session
from core.repositories import UserRepo
from core.services import ExpenseService

router = Router(name="expenses")

MENTION_RE = re.compile(r"@(\w+)")


@router.message(Command("add"))
async def cmd_add(message: Message) -> None:
    if not message.from_user or not message.chat:
        return

    if message.chat.type == "private":
        await message.answer("Эта команда работает только в групповых чатах.")
        return

    args = message.text or ""
    parts = args.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "Формат: /add <i>сумма описание @участник1 @участник2</i>\n"
            "Пример: /add 1500 ужин @alice @bob"
        )
        return

    _, body = parts
    tokens = body.split()

    try:
        amount = Decimal(tokens[0])
        if amount <= 0:
            raise InvalidOperation
    except (InvalidOperation, IndexError):
        await message.answer("❌ Укажите корректную сумму. Пример: /add 1500 ужин @alice @bob")
        return

    rest = " ".join(tokens[1:])
    mentions = MENTION_RE.findall(rest)
    description = MENTION_RE.sub("", rest).strip() or "расход"

    if not mentions:
        await message.answer("❌ Укажите хотя бы одного участника через @username.")
        return

    async with async_session() as session:
        user_repo = UserRepo(session)

        payer = await user_repo.get_or_create(
            user_id=message.from_user.id,
            username=message.from_user.username,
            full_name=message.from_user.full_name,
        )

        participant_ids: list[int] = [payer.id]

        entities = message.entities or []
        for entity in entities:
            if entity.type == "mention" and entity.user:
                u = await user_repo.get_or_create(
                    user_id=entity.user.id,
                    username=entity.user.username,
                    full_name=entity.user.full_name,
                )
                if u.id not in participant_ids:
                    participant_ids.append(u.id)
            elif entity.type == "text_mention" and entity.user:
                u = await user_repo.get_or_create(
                    user_id=entity.user.id,
                    username=entity.user.username,
                    full_name=entity.user.full_name or "",
                )
                if u.id not in participant_ids:
                    participant_ids.append(u.id)

        if len(participant_ids) < 2:
            for username in mentions:
                placeholder_id = hash(username) % (10**9)
                u = await user_repo.get_or_create(
                    user_id=placeholder_id,
                    username=username,
                    full_name=username,
                )
                if u.id not in participant_ids:
                    participant_ids.append(u.id)

        if len(participant_ids) < 2:
            await message.answer("❌ Нужно минимум 2 участника (вы + кто-то ещё).")
            return

        service = ExpenseService(session)
        await service.add_expense(
            group_id=message.chat.id,
            payer_id=payer.id,
            amount=amount,
            description=description,
            participant_ids=participant_ids,
        )

    share = amount / len(participant_ids)
    await message.answer(
        f"✅ <b>{description}</b> — {amount:.2f}\n"
        f"Оплатил: @{message.from_user.username or message.from_user.full_name}\n"
        f"Участники: {len(participant_ids)} чел. по {share:.2f} каждый"
    )


@router.message(Command("balance"))
async def cmd_balance(message: Message) -> None:
    if not message.chat:
        return

    if message.chat.type == "private":
        await message.answer("Эта команда работает только в групповых чатах.")
        return

    async with async_session() as session:
        service = ExpenseService(session)
        balances = await service.get_balances(message.chat.id)

    if not balances:
        await message.answer("📊 Нет активных расходов в этой группе.")
        return

    lines = ["📊 <b>Балансы:</b>"]
    user_repo_session = async_session()
    async with user_repo_session as session:
        for uid, balance in sorted(balances.items(), key=lambda x: x[1], reverse=True):
            from core.models import User

            user = await session.get(User, uid)
            name = (
                f"@{user.username}"
                if user and user.username
                else (user.full_name if user else str(uid))
            )
            sign = "+" if balance > 0 else ""
            lines.append(f"  {name}: {sign}{balance:.2f}")

    await message.answer("\n".join(lines))


@router.message(Command("settle"))
async def cmd_settle(message: Message) -> None:
    if not message.chat:
        return

    if message.chat.type == "private":
        await message.answer("Эта команда работает только в групповых чатах.")
        return

    async with async_session() as session:
        service = ExpenseService(session)
        settlements = await service.get_settlements(message.chat.id)

    if not settlements:
        await message.answer("✅ Все расчёты закрыты!")
        return

    lines = ["💸 <b>Оптимальные переводы:</b>"]
    async with async_session() as session:
        for debtor_id, creditor_id, amount in settlements:
            from core.models import User

            debtor = await session.get(User, debtor_id)
            creditor = await session.get(User, creditor_id)
            d_name = f"@{debtor.username}" if debtor and debtor.username else str(debtor_id)
            c_name = f"@{creditor.username}" if creditor and creditor.username else str(creditor_id)
            lines.append(f"  {d_name} → {c_name}: {amount:.2f}")

    await message.answer("\n".join(lines))


@router.message(Command("close"))
async def cmd_close(message: Message) -> None:
    if not message.chat:
        return

    if message.chat.type == "private":
        await message.answer("Эта команда работает только в групповых чатах.")
        return

    async with async_session() as session:
        service = ExpenseService(session)
        count = await service.settle_period(message.chat.id)

    if count == 0:
        await message.answer("Нет активных расходов для закрытия.")
    else:
        await message.answer(f"🔒 Период закрыт. Расходов закрыто: {count}.")
