import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.workspace import Workspace
from app.models.workspace_membership import WorkspaceMembership


async def create_workspace(
    session: AsyncSession, owner: User, name: str, description: str | None
) -> tuple[Workspace, WorkspaceMembership]:
    """Create a workspace with the given user as its sole `owner` member.

    One transaction: a workspace with no owning membership, or a membership
    with no workspace, must never be observable. Deliberately does not open
    an explicit `session.begin()`: the caller (`get_current_user`) already
    ran a `SELECT` on this same request-scoped session, which auto-begins a
    transaction, so a second explicit `begin()` here would conflict with it.
    Committing directly closes whatever transaction is already open.
    """
    workspace = Workspace(name=name, description=description)
    session.add(workspace)
    # workspace.id is a client-side default (uuid_pk()), only populated once
    # the INSERT is actually emitted, so flush before referencing it.
    await session.flush()
    membership = WorkspaceMembership(
        workspace_id=workspace.id, user_id=owner.id, role="owner"
    )
    session.add(membership)
    await session.commit()
    return workspace, membership


async def list_workspaces_for_user(
    session: AsyncSession, user_id: uuid.UUID
) -> list[tuple[Workspace, str, int]]:
    """The workspaces `user_id` belongs to, each with their role and the
    workspace's total member count, newest workspace first.

    Filters strictly by the caller's own memberships: a workspace never
    appears for a user who isn't a member of it.
    """
    member_count_subquery = (
        select(
            WorkspaceMembership.workspace_id,
            func.count().label("member_count"),
        )
        .group_by(WorkspaceMembership.workspace_id)
        .subquery()
    )

    statement = (
        select(
            Workspace, WorkspaceMembership.role, member_count_subquery.c.member_count
        )
        .join(WorkspaceMembership, WorkspaceMembership.workspace_id == Workspace.id)
        .join(
            member_count_subquery,
            member_count_subquery.c.workspace_id == Workspace.id,
        )
        .where(WorkspaceMembership.user_id == user_id)
        .order_by(Workspace.created_at.desc())
    )
    rows = (await session.execute(statement)).all()
    return [(workspace, role, member_count) for workspace, role, member_count in rows]
