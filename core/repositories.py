from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from core.models import Expense, ExpenseParticipant, Group, User


class UserRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, user_id: int, username: str | None, full_name: str) -> User:
        user = await self.session.get(User, user_id)
        if user is None:
            user = User(id=user_id, username=username, full_name=full_name)
            self.session.add(user)
            await self.session.flush()
        else:
            user.username = username
            user.full_name = full_name
        return user


class GroupRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_or_create(self, group_id: int, title: str) -> Group:
        group = await self.session.get(Group, group_id)
        if group is None:
            group = Group(id=group_id, title=title)
            self.session.add(group)
            await self.session.flush()
        else:
            group.title = title
        return group


class ExpenseRepo:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        group_id: int,
        payer_id: int,
        amount: Decimal,
        description: str,
        participant_ids: list[int],
    ) -> Expense:
        share = amount / len(participant_ids)
        expense = Expense(
            group_id=group_id,
            payer_id=payer_id,
            amount=float(amount),
            description=description,
        )
        self.session.add(expense)
        await self.session.flush()

        for uid in participant_ids:
            participant = ExpenseParticipant(
                expense_id=expense.id,
                user_id=uid,
                share=float(share),
            )
            self.session.add(participant)

        await self.session.flush()
        return expense

    async def get_unsettled_by_group(self, group_id: int) -> list[Expense]:
        stmt = (
            select(Expense)
            .where(Expense.group_id == group_id, Expense.is_settled.is_(False))
            .options(selectinload(Expense.participants).selectinload(ExpenseParticipant.user))
            .options(selectinload(Expense.payer))
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def settle_all(self, group_id: int) -> int:
        stmt = (
            update(Expense)
            .where(Expense.group_id == group_id, Expense.is_settled.is_(False))
            .values(is_settled=True)
        )
        result = await self.session.execute(stmt)
        return int(result.rowcount)  # type: ignore[attr-defined]
