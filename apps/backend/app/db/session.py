from collections.abc import AsyncIterator

from fastapi import Request
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import Settings


def create_engine(settings: Settings) -> AsyncEngine:
    return create_async_engine(settings.database_url, pool_pre_ping=True)


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )


async def get_session(request: Request) -> AsyncIterator[AsyncSession]:
    """Provide one `AsyncSession` per request.

    The session never commits implicitly. Application use cases own the
    transaction boundary (for example `async with session.begin():`); anything
    left uncommitted is rolled back when the session closes.
    """
    session_factory: async_sessionmaker[AsyncSession] | None = getattr(
        request.app.state, "session_factory", None
    )
    if session_factory is None:
        raise RuntimeError(
            "Database session factory is not initialised; "
            "the application lifespan has not run."
        )

    async with session_factory() as session:
        yield session
