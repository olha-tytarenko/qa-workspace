from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated

import httpx
import pytest
from fastapi import Depends, FastAPI
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from app.core.config import Settings, get_settings
from app.db.session import get_session
from app.main import create_app

pytestmark = pytest.mark.anyio

TEST_SETTINGS = Settings(database_url="postgresql+asyncpg://u:p@localhost/test")


def recording_session_factory(
    app: FastAPI, closed: list[AsyncSession]
) -> async_sessionmaker[AsyncSession]:
    """Session factory whose sessions append themselves to `closed` on close."""

    class RecordingSession(AsyncSession):
        async def close(self) -> None:
            closed.append(self)
            await super().close()

    return async_sessionmaker(
        bind=app.state.engine,
        class_=RecordingSession,
        autoflush=False,
        expire_on_commit=False,
    )


def create_test_app() -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
    return app


@asynccontextmanager
async def running(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield client


async def test_startup_fails_clearly_when_settings_are_unavailable(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    app = create_app()

    with pytest.raises(ValidationError) as error:
        async with app.router.lifespan_context(app):
            pass

    assert "database_url" in str(error.value)
    get_settings.cache_clear()


async def test_settings_dependency_can_be_overridden_for_tests() -> None:
    app = create_test_app()

    @app.get("/_settings")
    async def read_settings(
        settings: Annotated[Settings, Depends(get_settings)],
    ) -> dict[str, str]:
        return {"database_url": settings.database_url}

    async with running(app) as client:
        response = await client.get("/_settings")
        health = await client.get("/health")

    assert response.json() == {"database_url": TEST_SETTINGS.database_url}
    assert health.json() == {"status": "ok"}


async def test_one_session_per_request_is_closed_when_the_request_ends() -> None:
    app = create_test_app()
    closed: list[AsyncSession] = []
    used: list[AsyncSession] = []

    async def same_session_again(
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> AsyncSession:
        return session

    @app.get("/_session")
    async def read_session(
        session: Annotated[AsyncSession, Depends(get_session)],
        again: Annotated[AsyncSession, Depends(same_session_again)],
    ) -> dict[str, bool]:
        used.append(session)
        return {"shared_within_request": session is again}

    async with running(app) as client:
        app.state.session_factory = recording_session_factory(app, closed)
        first = await client.get("/_session")
        assert len(closed) == 1
        await client.get("/_session")

    assert first.json() == {"shared_within_request": True}
    assert closed == used
    assert used[0] is not used[1]


async def test_session_is_closed_when_the_handler_fails() -> None:
    app = create_test_app()
    closed: list[AsyncSession] = []

    @app.get("/_boom")
    async def boom(session: Annotated[AsyncSession, Depends(get_session)]) -> None:
        raise RuntimeError("boom")

    async with running(app) as client:
        app.state.session_factory = recording_session_factory(app, closed)
        with pytest.raises(RuntimeError):
            await client.get("/_boom")

    assert len(closed) == 1


async def test_session_dependency_requires_an_initialised_application() -> None:
    app = create_app()

    @app.get("/_session")
    async def read_session(
        session: Annotated[AsyncSession, Depends(get_session)],
    ) -> None:
        return None

    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        with pytest.raises(RuntimeError, match="not initialised"):
            await client.get("/_session")
