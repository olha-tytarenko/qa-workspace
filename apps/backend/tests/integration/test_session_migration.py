"""Schema checks for the `sessions` table introduced by the login slice.

`tests/integration/test_migrations.py` already proves the test database
reaches the Alembic head and has no model drift; these tests inspect the
resulting schema itself.
"""

from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import Connection, inspect, select
from sqlalchemy.engine.interfaces import (
    ReflectedForeignKeyConstraint,
    ReflectedUniqueConstraint,
)
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.session import Session
from app.models.user import User

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_sessions_table_has_the_expected_columns(
    db_session: AsyncSession,
) -> None:
    connection = await db_session.connection()

    def read_columns(sync_connection: Connection) -> set[str]:
        return {col["name"] for col in inspect(sync_connection).get_columns("sessions")}

    columns = await connection.run_sync(read_columns)

    assert columns == {"id", "user_id", "token_hash", "created_at", "expires_at"}


async def test_sessions_token_hash_unique_constraint_has_the_deterministic_name(
    db_session: AsyncSession,
) -> None:
    connection = await db_session.connection()

    def read_unique_constraints(
        sync_connection: Connection,
    ) -> list[ReflectedUniqueConstraint]:
        return inspect(sync_connection).get_unique_constraints("sessions")

    constraints = await connection.run_sync(read_unique_constraints)

    assert any(
        constraint["name"] == "uq_sessions_token_hash"
        and constraint["column_names"] == ["token_hash"]
        for constraint in constraints
    )


async def test_sessions_user_id_foreign_key_cascades_on_delete(
    db_session: AsyncSession,
) -> None:
    connection = await db_session.connection()

    def read_foreign_keys(
        sync_connection: Connection,
    ) -> list[ReflectedForeignKeyConstraint]:
        return inspect(sync_connection).get_foreign_keys("sessions")

    foreign_keys = await connection.run_sync(read_foreign_keys)

    assert any(
        fk["name"] == "fk_sessions_user_id_users"
        and fk["constrained_columns"] == ["user_id"]
        and fk["referred_table"] == "users"
        and fk["options"].get("ondelete") == "CASCADE"
        for fk in foreign_keys
    )


async def test_sessions_primary_key_has_the_deterministic_name(
    db_session: AsyncSession,
) -> None:
    connection = await db_session.connection()

    def read_pk_name(sync_connection: Connection) -> str | None:
        return inspect(sync_connection).get_pk_constraint("sessions")["name"]

    assert await connection.run_sync(read_pk_name) == "pk_sessions"


async def test_deleting_a_user_deletes_their_sessions(db_session: AsyncSession) -> None:
    user = User(email="cascade-check@example.com", password_hash="hash")
    async with db_session.begin():
        db_session.add(user)

    async with db_session.begin():
        db_session.add(
            Session(
                user_id=user.id,
                token_hash="a" * 64,
                expires_at=datetime.now(UTC) + timedelta(days=1),
            )
        )

    async with db_session.begin():
        await db_session.delete(user)

    remaining = (
        (await db_session.execute(select(Session).where(Session.user_id == user.id)))
        .scalars()
        .all()
    )
    assert remaining == []
