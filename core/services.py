from __future__ import annotations

from collections import defaultdict
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from core.models import Expense
from core.repositories import ExpenseRepo


def compute_balances(expenses: list[Expense]) -> dict[int, Decimal]:
    balances: dict[int, Decimal] = defaultdict(Decimal)
    for expense in expenses:
        balances[expense.payer_id] += Decimal(str(expense.amount))
        for p in expense.participants:
            balances[p.user_id] -= Decimal(str(p.share))
    return dict(balances)


def compute_settlements(balances: dict[int, Decimal]) -> list[tuple[int, int, Decimal]]:
    debtors: list[tuple[int, Decimal]] = []
    creditors: list[tuple[int, Decimal]] = []

    for uid, balance in balances.items():
        if balance < 0:
            debtors.append((uid, -balance))
        elif balance > 0:
            creditors.append((uid, balance))

    debtors.sort(key=lambda x: x[1], reverse=True)
    creditors.sort(key=lambda x: x[1], reverse=True)

    settlements: list[tuple[int, int, Decimal]] = []
    i, j = 0, 0

    while i < len(debtors) and j < len(creditors):
        debtor_id, debt = debtors[i]
        creditor_id, credit = creditors[j]
        amount = min(debt, credit)

        if amount > Decimal("0.01"):
            settlements.append((debtor_id, creditor_id, amount))

        debtors[i] = (debtor_id, debt - amount)
        creditors[j] = (creditor_id, credit - amount)

        if debtors[i][1] < Decimal("0.01"):
            i += 1
        if creditors[j][1] < Decimal("0.01"):
            j += 1

    return settlements


class ExpenseService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ExpenseRepo(session)

    async def add_expense(
        self,
        group_id: int,
        payer_id: int,
        amount: Decimal,
        description: str,
        participant_ids: list[int],
    ) -> Expense:
        expense = await self.repo.create(group_id, payer_id, amount, description, participant_ids)
        await self.session.commit()
        await self.session.refresh(expense, ["participants", "payer"])
        return expense

    async def get_balances(self, group_id: int) -> dict[int, Decimal]:
        expenses = await self.repo.get_unsettled_by_group(group_id)
        return compute_balances(expenses)

    async def get_settlements(self, group_id: int) -> list[tuple[int, int, Decimal]]:
        balances = await self.get_balances(group_id)
        return compute_settlements(balances)

    async def settle_period(self, group_id: int) -> int:
        count = await self.repo.settle_all(group_id)
        await self.session.commit()
        return count
