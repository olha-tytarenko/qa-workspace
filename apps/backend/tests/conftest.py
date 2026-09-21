from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from tests.database import TestDatabase, isolated_session, prepare_database


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
def test_database() -> TestDatabase:
    """The single, coordinated lifecycle of the PostgreSQL test database.

    Validates the configuration, recreates `qa_workspace_test` once, and migrates
    it to head, all before any test engine or connection exists. Tests must never
    drop or recreate the database themselves. Fails (not skips) when
    `TEST_DATABASE_URL` is missing or unsafe.
    """
    database = TestDatabase.from_environment()
    prepare_database(database)
    return database


@pytest.fixture
async def db_session(test_database: TestDatabase) -> AsyncIterator[AsyncSession]:
    """An async session on the test database that is rolled back after each test."""
    async with isolated_session(test_database) as session:
        yield session
