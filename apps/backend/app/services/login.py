from datetime import UTC, datetime

from fastapi import status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import ApplicationError
from app.core.security import (
    SESSION_TTL,
    generate_session_token,
    hash_session_token,
    verify_password,
)
from app.models.session import Session
from app.models.user import User


class InvalidCredentialsError(ApplicationError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "INVALID_CREDENTIALS"

    def __init__(self) -> None:
        # Deliberately identical whether the email doesn't exist or the
        # password is wrong, so a caller can't enumerate registered emails.
        super().__init__("Incorrect email or password.")


async def login_user(
    session: AsyncSession, email: str, password: str
) -> tuple[User, str, datetime]:
    """Verify credentials and create a session.

    `email` must already be normalized (trimmed, lowercased) by the caller's
    request schema. Returns the user, the raw session token, and its expiry;
    the raw token is never persisted or returned again — only its hash is
    stored (see `app.core.security.hash_session_token`).
    """
    async with session.begin():
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        if user is None or not verify_password(password, user.password_hash):
            raise InvalidCredentialsError()

        token = generate_session_token()
        expires_at = datetime.now(UTC) + SESSION_TTL
        session.add(
            Session(
                user_id=user.id,
                token_hash=hash_session_token(token),
                expires_at=expires_at,
            )
        )

    return user, token, expires_at
