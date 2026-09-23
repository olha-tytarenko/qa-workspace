"""Schema checks for the `users` table introduced by the registration slice.

`tests/integration/test_migrations.py` already proves the test database
reaches the Alembic head and has no model drift; these tests inspect the
resulting schema itself.
"""

import pytest
from sqlalchemy import Connection, inspect
from sqlalchemy.engine.interfaces import ReflectedUniqueConstraint
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_users_table_has_the_expected_columns(db_session: AsyncSession) -> None:
    connection = await db_session.connection()

    def read_columns(sync_connection: Connection) -> set[str]:
        return {col["name"] for col in inspect(sync_connection).get_columns("users")}

    columns = await connection.run_sync(read_columns)

    assert columns == {"id", "email", "password_hash", "created_at"}


async def test_users_email_unique_constraint_has_the_deterministic_name(
    db_session: AsyncSession,
) -> None:
    connection = await db_session.connection()

    def read_unique_constraints(
        sync_connection: Connection,
    ) -> list[ReflectedUniqueConstraint]:
        return inspect(sync_connection).get_unique_constraints("users")

    constraints = await connection.run_sync(read_unique_constraints)

    assert any(
        constraint["name"] == "uq_users_email"
        and constraint["column_names"] == ["email"]
        for constraint in constraints
    )


async def test_users_primary_key_has_the_deterministic_name(
    db_session: AsyncSession,
) -> None:
    connection = await db_session.connection()

    def read_pk_name(sync_connection: Connection) -> str | None:
        return inspect(sync_connection).get_pk_constraint("users")["name"]

    assert await connection.run_sync(read_pk_name) == "pk_users"


async def test_postgres_enforces_email_uniqueness(db_session: AsyncSession) -> None:
    async with db_session.begin():
        db_session.add(User(email="unique-check@example.com", password_hash="hash-a"))

    with pytest.raises(IntegrityError):
        async with db_session.begin():
            db_session.add(
                User(email="unique-check@example.com", password_hash="hash-b")
            )
