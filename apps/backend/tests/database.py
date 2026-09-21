"""PostgreSQL test-database support.

Lifecycle (driven by the session-scoped `test_database` fixture in conftest.py):

1. validate `TEST_DATABASE_URL` and refuse anything that could be a dev database;
2. drop and recreate the test database once, before any test connection exists;
3. run `alembic upgrade head` against it from empty;
4. tests open short-lived engines through `isolated_session` and dispose them.

Nothing in this module ever connects to the development database.
"""

import asyncio
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.engine import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.config import ASYNC_DATABASE_URL_PREFIX

BACKEND_DIR = Path(__file__).resolve().parents[1]
TEST_DATABASE_URL_ENV = "TEST_DATABASE_URL"
TEST_DATABASE_SUFFIX = "_test"
ADMIN_DATABASE = "postgres"


class UnsafeTestDatabaseError(RuntimeError):
    """The configured test database cannot be proven to be a safe test database."""


def validate_test_database_url(test_url: str, dev_url: str | None) -> URL:
    """Return the parsed test URL, or raise if it is not clearly a test database."""
    if not test_url.startswith(ASYNC_DATABASE_URL_PREFIX):
        raise UnsafeTestDatabaseError(
            f"{TEST_DATABASE_URL_ENV} must start with {ASYNC_DATABASE_URL_PREFIX!r}."
        )
    url = make_url(test_url)
    name = url.database
    if not name or not name.endswith(TEST_DATABASE_SUFFIX):
        raise UnsafeTestDatabaseError(
            f"{TEST_DATABASE_URL_ENV} must name a database ending in "
            f"{TEST_DATABASE_SUFFIX!r}, got {name!r}. Refusing to run tests."
        )
    if dev_url:
        dev = make_url(dev_url)
        if (dev.host, dev.port, dev.database) == (url.host, url.port, url.database):
            raise UnsafeTestDatabaseError(
                f"{TEST_DATABASE_URL_ENV} points at the same database as "
                "DATABASE_URL. Refusing to run tests."
            )
    return url


@dataclass(frozen=True)
class TestDatabase:
    """A validated test database. Can only be built through `from_environment`."""

    __test__ = False  # not a pytest test class

    url: URL
    admin_url: URL

    @classmethod
    def from_environment(cls) -> "TestDatabase":
        test_url = os.environ.get(TEST_DATABASE_URL_ENV)
        if not test_url:
            raise UnsafeTestDatabaseError(
                f"{TEST_DATABASE_URL_ENV} is not set. Database tests must be run "
                "through Docker Compose, which sets it "
                "(see docs/decisions.md and CLAUDE.md)."
            )
        url = validate_test_database_url(test_url, os.environ.get("DATABASE_URL"))
        return cls(url=url, admin_url=url.set(database=ADMIN_DATABASE))

    @property
    def name(self) -> str:
        assert self.url.database is not None
        return self.url.database


async def recreate_database(database: TestDatabase) -> None:
    """Drop (if present) and create the test database. Call once per session."""
    engine = create_async_engine(
        database.admin_url, isolation_level="AUTOCOMMIT", poolclass=NullPool
    )
    try:
        async with engine.connect() as connection:
            quoted = connection.dialect.identifier_preparer.quote(database.name)
            await connection.execute(
                text(f"DROP DATABASE IF EXISTS {quoted} WITH (FORCE)")
            )
            await connection.execute(text(f"CREATE DATABASE {quoted}"))
    finally:
        await engine.dispose()


def alembic_config(database: TestDatabase) -> Config:
    """Alembic config that targets the test database, never the settings URL."""
    config = Config(str(BACKEND_DIR / "alembic.ini"))
    config.attributes["database_url"] = database.url.render_as_string(
        hide_password=False
    )
    return config


def prepare_database(database: TestDatabase) -> None:
    """Recreate the test database and migrate it to head. Synchronous by design:
    Alembic's env.py starts its own event loop, so this must not run inside one."""
    asyncio.run(recreate_database(database))
    command.upgrade(alembic_config(database), "head")


@asynccontextmanager
async def isolated_session(database: TestDatabase) -> AsyncIterator[AsyncSession]:
    """A session whose work is always rolled back when the context exits.

    The session joins an outer connection-level transaction using savepoints, so
    code under test may call `session.commit()` or `async with session.begin()`
    and the changes are still discarded at the end. The engine and connection are
    closed on exit; nothing outlives the context.
    """
    engine = create_async_engine(database.url, poolclass=NullPool)
    try:
        async with engine.connect() as connection:
            outer = await connection.begin()
            session = AsyncSession(
                bind=connection,
                join_transaction_mode="create_savepoint",
                autoflush=False,
                expire_on_commit=False,
            )
            try:
                yield session
            finally:
                await session.close()
                await outer.rollback()
    finally:
        await engine.dispose()
