import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import hash_session_token
from app.main import create_app
from app.models.session import Session
from tests.database import TestDatabase

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

VALID_PASSWORD = "a sufficiently long password"
TRUSTED_ORIGIN = "http://frontend.test"


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def app_for(test_database: TestDatabase) -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        database_url=test_database.url.render_as_string(hide_password=False),
        cors_allowed_origins=TRUSTED_ORIGIN,
    )
    return app


@asynccontextmanager
async def running(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    """A client that behaves like the frontend: it sends the trusted `Origin`."""
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Origin": TRUSTED_ORIGIN},
        ) as client:
            yield client


async def sign_in(client: httpx.AsyncClient, email: str) -> str:
    """Logs `email` in on `client` and returns the raw session token."""
    response = await client.post(
        "/api/auth/login", json={"email": email, "password": VALID_PASSWORD}
    )
    assert response.status_code == 200
    return response.cookies["session"]


async def sign_up_and_sign_in(client: httpx.AsyncClient, prefix: str) -> str:
    email = unique_email(prefix)
    await client.post(
        "/api/auth/register", json={"email": email, "password": VALID_PASSWORD}
    )
    return await sign_in(client, email)


async def session_exists(db_session: AsyncSession, token: str) -> bool:
    row = await db_session.execute(
        select(Session.id).where(Session.token_hash == hash_session_token(token))
    )
    return row.scalar_one_or_none() is not None


def assert_clears_the_session_cookie(response: httpx.Response) -> None:
    set_cookie = response.headers.get("set-cookie")
    assert set_cookie is not None
    lowered = set_cookie.lower()
    assert lowered.startswith("session=")
    assert "max-age=0" in lowered
    assert "httponly" in lowered
    assert "samesite=lax" in lowered
    assert "path=/" in lowered


# --- successful logout ----------------------------------------------------------


async def test_logout_ends_the_session_and_clears_the_cookie(
    test_database: TestDatabase, db_session: AsyncSession
) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        token = await sign_up_and_sign_in(client, "alice")
        response = await client.post("/api/auth/logout")

    assert response.status_code == 204
    assert response.content == b""
    assert_clears_the_session_cookie(response)
    assert not await session_exists(db_session, token)


async def test_the_old_session_token_is_rejected_after_logout(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        token = await sign_up_and_sign_in(client, "bob")
        await client.post("/api/auth/logout")
        # Replay the token explicitly, as a client that ignored the cleared
        # cookie would.
        client.cookies.set("session", token)
        response = await client.get("/api/workspaces")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_logout_leaves_the_users_other_sessions_signed_in(
    test_database: TestDatabase, db_session: AsyncSession
) -> None:
    app = app_for(test_database)

    async with running(app) as first_device:
        email = unique_email("carol")
        await first_device.post(
            "/api/auth/register", json={"email": email, "password": VALID_PASSWORD}
        )
        first_token = await sign_in(first_device, email)

        async with running(app) as second_device:
            second_token = await sign_in(second_device, email)
            await second_device.post("/api/auth/logout")

        still_signed_in = await first_device.get("/api/workspaces")

    assert still_signed_in.status_code == 200
    assert await session_exists(db_session, first_token)
    assert not await session_exists(db_session, second_token)


# --- idempotency ------------------------------------------------------------------


async def test_logout_without_a_session_cookie_still_succeeds(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        response = await client.post("/api/auth/logout")

    assert response.status_code == 204
    assert_clears_the_session_cookie(response)


async def test_logout_with_an_unknown_token_still_succeeds(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        client.cookies.set("session", "not-a-real-session-token")
        response = await client.post("/api/auth/logout")

    assert response.status_code == 204
    assert_clears_the_session_cookie(response)


# --- origin validation ----------------------------------------------------------


@pytest.mark.parametrize(
    "origin_headers",
    [{"Origin": "http://evil.example.com"}, {}],
    ids=["untrusted_origin", "missing_origin"],
)
async def test_logout_from_an_untrusted_origin_returns_403_and_keeps_the_session(
    test_database: TestDatabase,
    db_session: AsyncSession,
    origin_headers: dict[str, str],
) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        token = await sign_up_and_sign_in(client, "dave")
        del client.headers["Origin"]
        response = await client.post("/api/auth/logout", headers=origin_headers)

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ORIGIN_NOT_ALLOWED"
    assert "set-cookie" not in response.headers
    assert await session_exists(db_session, token)
