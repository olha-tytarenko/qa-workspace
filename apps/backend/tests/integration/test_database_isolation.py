import os

import pytest
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import AsyncSession

from tests.database import TestDatabase, isolated_session

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

# The probe table exists only inside rolled-back transactions on the test
# database. It is raw SQL: never ORM metadata, never an Alembic migration.
CREATE_PROBE = "CREATE TABLE isolation_probe (id integer PRIMARY KEY)"
PROBE_EXISTS = "SELECT to_regclass('isolation_probe') IS NOT NULL"


async def probe_exists(session: AsyncSession) -> bool:
    return bool((await session.execute(text(PROBE_EXISTS))).scalar_one())


async def test_uses_a_real_postgresql_test_database(
    db_session: AsyncSession, test_database: TestDatabase
) -> None:
    version = (await db_session.execute(text("SELECT version()"))).scalar_one()
    current = (await db_session.execute(text("SELECT current_database()"))).scalar_one()

    assert db_session.bind.dialect.name == "postgresql"
    assert "PostgreSQL" in version
    assert current == test_database.name == "qa_workspace_test"
    dev_url = os.environ.get("DATABASE_URL")
    if dev_url:
        assert current != make_url(dev_url).database


async def test_committed_work_is_discarded_when_the_session_context_ends(
    test_database: TestDatabase,
) -> None:
    async with isolated_session(test_database) as session:
        async with session.begin():
            await session.execute(text(CREATE_PROBE))
            await session.execute(text("INSERT INTO isolation_probe VALUES (1)"))
        # The explicit transaction above was committed (released its savepoint).
        assert await probe_exists(session)

    async with isolated_session(test_database) as fresh:
        assert not await probe_exists(fresh)


async def test_uncommitted_and_savepoint_work_is_invisible_to_other_sessions(
    test_database: TestDatabase,
) -> None:
    async with isolated_session(test_database) as first:
        async with first.begin():
            await first.execute(text(CREATE_PROBE))

        async with isolated_session(test_database) as second:
            assert await probe_exists(first)
            assert not await probe_exists(second)


async def test_a_failed_explicit_transaction_rolls_back_only_its_own_work(
    db_session: AsyncSession,
) -> None:
    async with db_session.begin():
        await db_session.execute(text(CREATE_PROBE))

    with pytest.raises(RuntimeError, match="abort"):
        async with db_session.begin():
            await db_session.execute(text("INSERT INTO isolation_probe VALUES (1)"))
            raise RuntimeError("abort")

    async with db_session.begin():
        count = (
            await db_session.execute(text("SELECT count(*) FROM isolation_probe"))
        ).scalar_one()
    assert count == 0
