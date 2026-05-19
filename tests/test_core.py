from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from core.models import Base
from core.repositories import GroupRepo, UserRepo
from core.services import ExpenseService, compute_balances, compute_settlements


@pytest.fixture
async def session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_sess = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_sess() as s:
        yield s

    await engine.dispose()


async def test_user_get_or_create(session: AsyncSession):
    repo = UserRepo(session)
    user = await repo.get_or_create(123, "alice", "Alice")
    assert user.id == 123
    assert user.username == "alice"

    user2 = await repo.get_or_create(123, "alice_new", "Alice New")
    assert user2.id == 123
    assert user2.username == "alice_new"


async def test_group_get_or_create(session: AsyncSession):
    repo = GroupRepo(session)
    group = await repo.get_or_create(-100, "Test Group")
    assert group.id == -100
    assert group.title == "Test Group"


async def test_add_expense(session: AsyncSession):
    user_repo = UserRepo(session)
    await user_repo.get_or_create(1, "alice", "Alice")
    await user_repo.get_or_create(2, "bob", "Bob")
    await user_repo.get_or_create(3, "carol", "Carol")

    group_repo = GroupRepo(session)
    await group_repo.get_or_create(-100, "Group")

    service = ExpenseService(session)
    expense = await service.add_expense(
        group_id=-100,
        payer_id=1,
        amount=Decimal("1500"),
        description="dinner",
        participant_ids=[1, 2, 3],
    )
    assert expense.id is not None
    assert len(expense.participants) == 3


async def test_balances(session: AsyncSession):
    user_repo = UserRepo(session)
    await user_repo.get_or_create(1, "alice", "Alice")
    await user_repo.get_or_create(2, "bob", "Bob")

    group_repo = GroupRepo(session)
    await group_repo.get_or_create(-100, "Group")

    service = ExpenseService(session)
    await service.add_expense(
        group_id=-100,
        payer_id=1,
        amount=Decimal("100"),
        description="coffee",
        participant_ids=[1, 2],
    )

    balances = await service.get_balances(-100)
    assert balances[1] == Decimal("50")
    assert balances[2] == Decimal("-50")


async def test_settlements(session: AsyncSession):
    user_repo = UserRepo(session)
    await user_repo.get_or_create(1, "alice", "Alice")
    await user_repo.get_or_create(2, "bob", "Bob")
    await user_repo.get_or_create(3, "carol", "Carol")

    group_repo = GroupRepo(session)
    await group_repo.get_or_create(-100, "Group")

    service = ExpenseService(session)
    await service.add_expense(
        group_id=-100,
        payer_id=1,
        amount=Decimal("300"),
        description="lunch",
        participant_ids=[1, 2, 3],
    )

    settlements = await service.get_settlements(-100)
    assert len(settlements) == 2
    total_settled = sum(s[2] for s in settlements)
    assert total_settled == Decimal("200")


async def test_settle_period(session: AsyncSession):
    user_repo = UserRepo(session)
    await user_repo.get_or_create(1, "alice", "Alice")
    await user_repo.get_or_create(2, "bob", "Bob")

    group_repo = GroupRepo(session)
    await group_repo.get_or_create(-100, "Group")

    service = ExpenseService(session)
    await service.add_expense(
        group_id=-100,
        payer_id=1,
        amount=Decimal("200"),
        description="taxi",
        participant_ids=[1, 2],
    )

    count = await service.settle_period(-100)
    assert count == 1

    balances = await service.get_balances(-100)
    assert len(balances) == 0


def test_compute_settlements_empty():
    result = compute_settlements({})
    assert result == []


def test_compute_balances_empty():
    result = compute_balances([])
    assert result == {}
