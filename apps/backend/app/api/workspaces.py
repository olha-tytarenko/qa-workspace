from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user
from app.db.session import get_session
from app.models.user import User
from app.schemas.workspace import (
    WorkspaceCreateRequest,
    WorkspaceListResponse,
    WorkspaceResponse,
    WorkspaceSummary,
)
from app.services.workspaces import create_workspace, list_workspaces_for_user

router = APIRouter()


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=WorkspaceResponse,
)
async def create(
    payload: WorkspaceCreateRequest,
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorkspaceResponse:
    workspace, membership = await create_workspace(
        session, current_user, payload.name, payload.description
    )
    return WorkspaceResponse(
        data=WorkspaceSummary(
            id=workspace.id,
            name=workspace.name,
            description=workspace.description,
            created_at=workspace.created_at,
            role=membership.role,
            member_count=1,
        )
    )


@router.get(
    "",
    status_code=status.HTTP_200_OK,
    response_model=WorkspaceListResponse,
)
async def list_mine(
    session: Annotated[AsyncSession, Depends(get_session)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> WorkspaceListResponse:
    rows = await list_workspaces_for_user(session, current_user.id)
    return WorkspaceListResponse(
        items=[
            WorkspaceSummary(
                id=workspace.id,
                name=workspace.name,
                description=workspace.description,
                created_at=workspace.created_at,
                role=role,
                member_count=member_count,
            )
            for workspace, role, member_count in rows
        ]
    )
