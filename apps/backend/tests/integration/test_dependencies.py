import uuid
from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import UnauthenticatedError, get_current_user
from app.core.security import generate_session_token, hash_session_token
from app.models.session import Session
from app.models.user import User

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


async def create_user_with_session(
    db_session: AsyncSession, *, expires_at: datetime
) -> tuple[User, str]:
    user = User(email=unique_email("dep-check"), password_hash="hash")
    async with db_session.begin():
        db_session.add(user)

    token = generate_session_token()
    async with db_session.begin():
        db_session.add(
            Session(
                user_id=user.id,
                token_hash=hash_session_token(token),
                expires_at=expires_at,
            )
        )
    return user, token


async def test_returns_the_user_for_a_valid_session(db_session: AsyncSession) -> None:
    user, token = await create_user_with_session(
        db_session, expires_at=datetime.now(UTC) + timedelta(days=1)
    )

    resolved = await get_current_user(db_session, token)

    assert resolved.id == user.id


async def test_raises_when_no_cookie_is_present(db_session: AsyncSession) -> None:
    with pytest.raises(UnauthenticatedError):
        await get_current_user(db_session, None)


async def test_raises_for_an_unknown_token(db_session: AsyncSession) -> None:
    with pytest.raises(UnauthenticatedError):
        await get_current_user(db_session, generate_session_token())


async def test_raises_for_an_expired_session(db_session: AsyncSession) -> None:
    _user, token = await create_user_with_session(
        db_session, expires_at=datetime.now(UTC) - timedelta(minutes=1)
    )

    with pytest.raises(UnauthenticatedError):
        await get_current_user(db_session, token)
