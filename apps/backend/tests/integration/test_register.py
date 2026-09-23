import logging
import uuid
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings, get_settings
from app.core.security import verify_password
from app.main import create_app
from app.models.user import User
from app.services.registration import EmailAlreadyRegisteredError, register_user
from tests.database import TestDatabase

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

VALID_PASSWORD = "a sufficiently long password"


def unique_email(prefix: str) -> str:
    # Each API-level test here goes through the app's own engine and really
    # commits (it exercises the real request/session lifecycle, unlike
    # `db_session`, which rolls back). A unique email per test avoids
    # colliding with rows other tests in the same session have committed.
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
        # `raise_app_exceptions=False`: Starlette's `ServerErrorMiddleware`
        # always re-raises an unhandled exception after sending its 500
        # response (so a real ASGI server can log it); without this, that
        # re-raise would propagate through the test instead of letting it
        # inspect the response the catch-all handler produced.
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


# --- successful registration -------------------------------------------------


async def test_valid_registration_returns_201_with_the_public_user_shape(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)
    email = unique_email("alice")

    async with running(app) as client:
        response = await register(client, email)

    assert response.status_code == 201
    body = response.json()
    assert set(body.keys()) == {"data"}
    assert set(body["data"].keys()) == {"id", "email", "created_at"}
    assert body["data"]["email"] == email


async def test_email_is_trimmed_and_lowercased_before_persistence(
    test_database: TestDatabase, db_session: AsyncSession
) -> None:
    app = app_for(test_database)
    local_part = uuid.uuid4().hex[:8]
    submitted = f"  {local_part}@Example.COM  "
    normalized = f"{local_part}@example.com"

    async with running(app) as client:
        response = await register(client, submitted)

    assert response.status_code == 201
    assert response.json()["data"]["email"] == normalized

    user = (
        await db_session.execute(select(User).where(User.email == normalized))
    ).scalar_one()
    assert user.email == normalized


async def test_stored_password_is_an_argon2id_hash_that_verifies(
    test_database: TestDatabase, db_session: AsyncSession
) -> None:
    app = app_for(test_database)
    email = unique_email("bob")

    async with running(app) as client:
        await register(client, email)

    user = (
        await db_session.execute(select(User).where(User.email == email))
    ).scalar_one()
    assert user.password_hash != VALID_PASSWORD
    assert verify_password(VALID_PASSWORD, user.password_hash)


async def test_two_different_users_can_register(test_database: TestDatabase) -> None:
    app = app_for(test_database)
    first_email, second_email = unique_email("first"), unique_email("second")

    async with running(app) as client:
        first = await register(client, first_email)
        second = await register(client, second_email)

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.json()["data"]["id"] != second.json()["data"]["id"]


# --- validation ----------------------------------------------------------------


@pytest.mark.parametrize(
    "make_payload",
    [
        lambda email: {"password": VALID_PASSWORD},
        lambda email: {"email": "not-an-email", "password": VALID_PASSWORD},
        lambda email: {"email": email},
        lambda email: {"email": email, "password": "short"},
        lambda email: {"email": email, "password": "x" * 129},
    ],
    ids=[
        "missing_email",
        "invalid_email",
        "missing_password",
        "password_too_short",
        "password_too_long",
    ],
)
async def test_invalid_requests_return_422_with_the_error_envelope(
    test_database: TestDatabase,
    make_payload: Callable[[str], dict[str, str]],
) -> None:
    app = app_for(test_database)
    payload = make_payload(unique_email("invalid"))

    async with running(app) as client:
        response = await client.post("/api/auth/register", json=payload)

    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "VALIDATION_ERROR"
    assert "request_id" in body


async def test_unexpected_fields_are_rejected(test_database: TestDatabase) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        response = await client.post(
            "/api/auth/register",
            json={
                "email": unique_email("extra"),
                "password": VALID_PASSWORD,
                "name": "Alice",
            },
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_validation_error_does_not_echo_the_submitted_password(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        response = await client.post(
            "/api/auth/register",
            json={"email": unique_email("short"), "password": "too-short"},
        )

    assert "too-short" not in response.text


# --- duplicate registration ----------------------------------------------------


async def test_exact_duplicate_email_returns_409(test_database: TestDatabase) -> None:
    app = app_for(test_database)
    email = unique_email("dup")

    async with running(app) as client:
        first = await register(client, email)
        second = await register(client, email)

    assert first.status_code == 201
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "EMAIL_ALREADY_REGISTERED"


async def test_case_variant_duplicate_email_returns_409(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)
    local_part = uuid.uuid4().hex[:8]

    async with running(app) as client:
        first = await register(client, f"{local_part}@example.com")
        second = await register(client, f"{local_part.upper()}@EXAMPLE.com")

    assert first.status_code == 201
    assert second.status_code == 409


async def test_whitespace_variant_duplicate_email_returns_409(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)
    local_part = uuid.uuid4().hex[:8]

    async with running(app) as client:
        first = await register(client, f"{local_part}@example.com")
        second = await register(client, f"  {local_part}@example.com  ")

    assert first.status_code == 201
    assert second.status_code == 409


async def test_the_existing_user_is_unchanged_after_a_duplicate_conflict(
    test_database: TestDatabase, db_session: AsyncSession
) -> None:
    app = app_for(test_database)
    email = unique_email("stable")

    async with running(app) as client:
        first = await register(client, email)
        await register(client, email)

    user = (
        await db_session.execute(select(User).where(User.email == email))
    ).scalar_one()
    assert str(user.id) == first.json()["data"]["id"]


async def test_service_session_remains_usable_after_a_duplicate_conflict(
    db_session: AsyncSession,
) -> None:
    email = unique_email("session-reuse")

    await register_user(db_session, email, VALID_PASSWORD)

    with pytest.raises(EmailAlreadyRegisteredError):
        await register_user(db_session, email, VALID_PASSWORD)

    # The same session must still be usable for an unrelated operation.
    other_email = unique_email("session-reuse-again")
    other_user = await register_user(db_session, other_email, VALID_PASSWORD)
    assert other_user.email == other_email


# --- security --------------------------------------------------------------------


async def test_response_never_contains_the_password_or_its_hash(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        response = await register(client, unique_email("secure"))

    assert VALID_PASSWORD not in response.text
    data = response.json()["data"]
    assert "password" not in data
    assert "password_hash" not in data


async def test_plaintext_password_never_appears_in_captured_logs(
    test_database: TestDatabase, caplog: pytest.LogCaptureFixture
) -> None:
    app = app_for(test_database)
    password = "a-very-distinctive-password-value-for-this-test"

    with caplog.at_level(logging.DEBUG):
        async with running(app) as client:
            await register(client, unique_email("logged"), password)

    assert password not in caplog.text


async def test_unexpected_errors_do_not_expose_internal_details(
    test_database: TestDatabase, monkeypatch: pytest.MonkeyPatch
) -> None:
    app = app_for(test_database)

    async def boom(*args: object, **kwargs: object) -> None:
        raise RuntimeError("division by zero at db/internal/query.py:42")

    monkeypatch.setattr("app.api.auth.register_user", boom)

    async with running(app) as client:
        response = await client.post(
            "/api/auth/register",
            json={"email": unique_email("boom"), "password": VALID_PASSWORD},
        )

    assert response.status_code == 500
    body = response.json()["error"]
    assert body["code"] == "INTERNAL_ERROR"
    assert "division by zero" not in response.text
    assert "query.py" not in response.text
