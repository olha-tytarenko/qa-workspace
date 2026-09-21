"""Migration smoke tests.

The `test_database` fixture has already recreated the database and run
`alembic upgrade head` from empty exactly once for the session. These tests only
inspect the result; they never drop or recreate the database.

Limitation: there are no migrations yet, so head is the empty revision. These
tests prove that Alembic can reach the test database and that model metadata has
no drift. They become a real schema check once the first migration exists.
"""

import asyncio
import logging

import pytest
from alembic import command
from alembic.runtime.migration import MigrationContext
from alembic.script import ScriptDirectory
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from tests.database import TestDatabase, alembic_config

pytestmark = pytest.mark.integration


async def current_revisions(database: TestDatabase) -> set[str]:
    engine = create_async_engine(database.url, poolclass=NullPool)

    def read(connection: Connection) -> set[str]:
        return set(MigrationContext.configure(connection).get_current_heads())

    try:
        async with engine.connect() as connection:
            return await connection.run_sync(read)
    finally:
        await engine.dispose()


def test_database_is_at_the_alembic_head(test_database: TestDatabase) -> None:
    heads = set(ScriptDirectory.from_config(alembic_config(test_database)).get_heads())

    assert asyncio.run(current_revisions(test_database)) == heads


def test_model_metadata_has_no_drift_from_the_migrated_schema(
    test_database: TestDatabase,
) -> None:
    # Raises if autogenerate would produce any operation.
    command.check(alembic_config(test_database))


def test_running_alembic_in_process_keeps_application_loggers_enabled(
    test_database: TestDatabase,
) -> None:
    # env.py applies alembic.ini's logging config. That must not silence loggers
    # the application (or a later caplog-based test) already created.
    application_logger = logging.getLogger("app.alembic_logging_probe")
    assert not application_logger.disabled

    command.check(alembic_config(test_database))

    assert not application_logger.disabled
