from datetime import UTC, datetime
from typing import Annotated

from fastapi import Cookie, Depends, Header, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.errors import ApplicationError
from app.core.security import SESSION_COOKIE_NAME, hash_session_token
from app.db.session import get_session
from app.models.session import Session
from app.models.user import User


class UnauthenticatedError(ApplicationError):
    status_code = status.HTTP_401_UNAUTHORIZED
    code = "UNAUTHENTICATED"

    def __init__(self) -> None:
        super().__init__("Authentication is required.")


class OriginNotAllowedError(ApplicationError):
    status_code = status.HTTP_403_FORBIDDEN
    code = "ORIGIN_NOT_ALLOWED"

    def __init__(self) -> None:
        super().__init__("The request origin is not allowed.")


async def require_trusted_origin(
    settings: Annotated[Settings, Depends(get_settings)],
    origin: Annotated[str | None, Header()] = None,
) -> None:
    """Reject a cookie-authenticated mutation from an untrusted `Origin`.

    CSRF protection for state-changing requests that rely on the session
    cookie (docs/decisions.md §2). The trusted origins are the CORS allowlist.
    A missing `Origin` is rejected too: browsers send it on every `POST`, so
    its absence never comes from the legitimate frontend.
    """
    if origin is None or origin not in settings.cors_origins:
        raise OriginNotAllowedError()


async def get_current_user(
    session: Annotated[AsyncSession, Depends(get_session)],
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE_NAME)] = None,
) -> User:
    """Resolve the authenticated user from the session cookie.

    Raises `UnauthenticatedError` when the cookie is missing, references no
    session, or references an expired one. This is the first place that
    actually checks `Session.expires_at`.
    """
    if session_token is None:
        raise UnauthenticatedError()

    result = await session.execute(
        select(User)
        .join(Session, Session.user_id == User.id)
        .where(
            Session.token_hash == hash_session_token(session_token),
            Session.expires_at > datetime.now(UTC),
        )
    )
    user = result.scalar_one_or_none()
    if user is None:
        raise UnauthenticatedError()
    return user
