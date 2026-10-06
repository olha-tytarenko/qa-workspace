from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_session_token
from app.models.session import Session


async def logout_session(session: AsyncSession, token: str) -> None:
    """Delete the session identified by `token`, if any.

    Only that one session ends; the user's other sessions are untouched. An
    unknown or already-expired token is not an error, so logout is idempotent.
    """
    async with session.begin():
        await session.execute(
            delete(Session).where(Session.token_hash == hash_session_token(token))
        )
