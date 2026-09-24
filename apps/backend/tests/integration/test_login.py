import logging
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta

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


def unique_email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}@example.com"


def app_for(test_database: TestDatabase) -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        database_url=test_database.url.render_as_string(hide_password=False),
    )
    return app


@asynccontextmanager
async def running(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app, raise_app_exceptions=False)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield client


async def register(
    client: httpx.AsyncClient, email: str, password: str = VALID_PASSWORD
) -> httpx.Response:
    return await client.post(
        "/api/auth/register", json={"email": email, "password": password}
    )


async def login(
    client: httpx.AsyncClient, email: str, password: str = VALID_PASSWORD
) -> httpx.Response:
    return await client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )


# --- successful login ---------------------------------------------------


async def test_valid_login_returns_200_with_the_public_user_shape(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)
    email = unique_email("alice")

    async with running(app) as client:
        await register(client, email)
        response = await login(client, email)

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {"data"}
    assert set(body["data"].keys()) == {"id", "email", "created_at"}
    assert body["data"]["email"] == email


async def test_login_sets_a_session_cookie_with_the_expected_attributes(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)
    email = unique_email("bob")

    async with running(app) as client:
        await register(client, email)
        response = await login(client, email)

    set_cookie = response.headers.get("set-cookie")
    assert set_cookie is not None
    assert "session=" in set_cookie
    assert "httponly" in set_cookie.lower()
    assert "samesite=lax" in set_cookie.lower()
    # Not Secure by default in the test settings (local HTTP, matches
    # SESSION_COOKIE_SECURE=false).
    assert "secure" not in set_cookie.lower()
    assert "max-age=" in set_cookie.lower()
    assert response.cookies.get("session")


async def test_a_session_row_is_created_with_the_correct_hash_and_expiry(
    test_database: TestDatabase, db_session: AsyncSession
) -> None:
    app = app_for(test_database)
    email = unique_email("carol")

    async with running(app) as client:
        await register(client, email)
        response = await login(client, email)

    token = response.cookies["session"]
    session_row = (
        await db_session.execute(
            select(Session).where(Session.token_hash == hash_session_token(token))
        )
    ).scalar_one()

    now = datetime.now(UTC)
    assert (
        now + timedelta(days=13, hours=23)
        < session_row.expires_at
        < now + timedelta(days=14, minutes=1)
    )


async def test_login_normalizes_email_the_same_way_as_registration(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)
    local_part = uuid.uuid4().hex[:8]
    registered_email = f"{local_part}@example.com"

    async with running(app) as client:
        await register(client, registered_email)
        response = await login(client, f"  {local_part}@EXAMPLE.com  ")

    assert response.status_code == 200


# --- invalid credentials --------------------------------------------------


async def test_wrong_password_and_nonexistent_email_return_identical_responses(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)
    email = unique_email("erin")

    async with running(app) as client:
        await register(client, email)
        wrong_password = await login(
            client, email, password="a different long password"
        )
        no_such_user = await login(client, unique_email("ghost"))

    assert wrong_password.status_code == no_such_user.status_code == 401
    wrong_body = wrong_password.json()["error"]
    ghost_body = no_such_user.json()["error"]
    assert wrong_body["code"] == ghost_body["code"] == "INVALID_CREDENTIALS"
    assert wrong_body["message"] == ghost_body["message"]
    assert "set-cookie" not in wrong_password.headers
    assert "set-cookie" not in no_such_user.headers


# --- validation -------------------------------------------------------------


@pytest.mark.parametrize(
    "make_payload",
    [
        lambda email: {"password": VALID_PASSWORD},
        lambda email: {"email": "not-an-email", "password": VALID_PASSWORD},
        lambda email: {"email": email},
        lambda email: {"email": email, "password": ""},
    ],
    ids=["missing_email", "invalid_email", "missing_password", "empty_password"],
)
async def test_invalid_requests_return_422_with_the_error_envelope(
    test_database: TestDatabase,
    make_payload: Callable[[str], dict[str, str]],
) -> None:
    app = app_for(test_database)
    payload = make_payload(unique_email("invalid"))

    async with running(app) as client:
        response = await client.post("/api/auth/login", json=payload)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_unexpected_fields_are_rejected(test_database: TestDatabase) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        response = await client.post(
            "/api/auth/login",
            json={
                "email": unique_email("extra"),
                "password": VALID_PASSWORD,
                "remember": True,
            },
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


# --- security -----------------------------------------------------------------


async def test_response_never_contains_the_password_hash_or_raw_token(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)
    email = unique_email("frank")

    async with running(app) as client:
        await register(client, email)
        response = await login(client, email)

    assert VALID_PASSWORD not in response.text
    data = response.json()["data"]
    assert "password" not in data
    assert "password_hash" not in data
    token = response.cookies["session"]
    assert token not in response.json()["data"].values()


async def test_plaintext_password_never_appears_in_captured_logs(
    test_database: TestDatabase, caplog: pytest.LogCaptureFixture
) -> None:
    app = app_for(test_database)
    email = unique_email("grace")
    password = "a-very-distinctive-login-password-value"

    async with running(app) as client:
        await register(client, email, password)
        with caplog.at_level(logging.DEBUG):
            await login(client, email, password)

    assert password not in caplog.text


async def test_unexpected_errors_do_not_expose_internal_details(
    test_database: TestDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = app_for(test_database)

    async def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("division by zero at db/internal/query.py:42")

    monkeypatch.setattr("app.api.auth.login_user", boom)

    async with running(app) as client:
        response = await client.post(
            "/api/auth/login",
            json={"email": unique_email("boom"), "password": VALID_PASSWORD},
        )

    assert response.status_code == 500
    body = response.json()["error"]
    assert body["code"] == "INTERNAL_ERROR"
    assert "division by zero" not in response.text
    assert "query.py" not in response.text
