"""Schema checks for the `workspaces` and `workspace_memberships` tables.

`tests/integration/test_migrations.py` already proves the test database
reaches the Alembic head and has no model drift; these tests inspect the
resulting schema itself.
"""

import pytest
from sqlalchemy import Connection, inspect, select
from sqlalchemy.engine.interfaces import (
    ReflectedForeignKeyConstraint,
    ReflectedUniqueConstraint,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_membership import WorkspaceMembership

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


async def test_workspaces_table_has_the_expected_columns(
    db_session: AsyncSession,
) -> None:
    connection = await db_session.connection()

    def read_columns(sync_connection: Connection) -> set[str]:
        return {
            col["name"] for col in inspect(sync_connection).get_columns("workspaces")
        }

    columns = await connection.run_sync(read_columns)

    assert columns == {"id", "name", "description", "created_at"}


async def test_workspace_memberships_table_has_the_expected_columns(
    db_session: AsyncSession,
) -> None:
    connection = await db_session.connection()

    def read_columns(sync_connection: Connection) -> set[str]:
        return {
            col["name"]
            for col in inspect(sync_connection).get_columns("workspace_memberships")
        }

    columns = await connection.run_sync(read_columns)

    assert columns == {"id", "workspace_id", "user_id", "role", "created_at"}


async def test_workspace_memberships_unique_constraint_has_the_deterministic_name(
    db_session: AsyncSession,
) -> None:
    connection = await db_session.connection()

    def read_unique_constraints(
        sync_connection: Connection,
    ) -> list[ReflectedUniqueConstraint]:
        return inspect(sync_connection).get_unique_constraints("workspace_memberships")

    constraints = await connection.run_sync(read_unique_constraints)

    assert any(
        constraint["name"] == "uq_workspace_memberships_workspace_id_user_id"
        and set(constraint["column_names"]) == {"workspace_id", "user_id"}
        for constraint in constraints
    )


async def test_workspace_memberships_foreign_keys_cascade_on_delete(
    db_session: AsyncSession,
) -> None:
    connection = await db_session.connection()

    def read_foreign_keys(
        sync_connection: Connection,
    ) -> list[ReflectedForeignKeyConstraint]:
        return inspect(sync_connection).get_foreign_keys("workspace_memberships")

    foreign_keys = await connection.run_sync(read_foreign_keys)

    assert any(
        fk["name"] == "fk_workspace_memberships_user_id_users"
        and fk["constrained_columns"] == ["user_id"]
        and fk["options"].get("ondelete") == "CASCADE"
        for fk in foreign_keys
    )
    assert any(
        fk["name"] == "fk_workspace_memberships_workspace_id_workspaces"
        and fk["constrained_columns"] == ["workspace_id"]
        and fk["options"].get("ondelete") == "CASCADE"
        for fk in foreign_keys
    )


async def test_workspace_memberships_role_check_constraint_rejects_invalid_values(
    db_session: AsyncSession,
) -> None:
    user = User(email="role-check@example.com", password_hash="hash")
    async with db_session.begin():
        db_session.add(user)

    workspace = Workspace(name="Role check workspace")
    async with db_session.begin():
        db_session.add(workspace)

    with pytest.raises(IntegrityError):
        async with db_session.begin():
            db_session.add(
                WorkspaceMembership(
                    workspace_id=workspace.id, user_id=user.id, role="not-a-real-role"
                )
            )


async def test_deleting_a_workspace_deletes_its_memberships(
    db_session: AsyncSession,
) -> None:
    user = User(email="cascade-workspace@example.com", password_hash="hash")
    async with db_session.begin():
        db_session.add(user)

    workspace = Workspace(name="Deletable workspace")
    async with db_session.begin():
        db_session.add(workspace)

    async with db_session.begin():
        db_session.add(
            WorkspaceMembership(
                workspace_id=workspace.id, user_id=user.id, role="owner"
            )
        )

    async with db_session.begin():
        await db_session.delete(workspace)

    remaining = (
        (
            await db_session.execute(
                select(WorkspaceMembership).where(
                    WorkspaceMembership.workspace_id == workspace.id
                )
            )
        )
        .scalars()
        .all()
    )
    assert remaining == []
