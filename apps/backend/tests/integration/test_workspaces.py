import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI

from app.core.config import Settings, get_settings
from app.main import create_app
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


async def sign_up_and_sign_in(client: httpx.AsyncClient, prefix: str) -> str:
    """Registers a fresh user and logs them in on `client`, returning their email.

    The client's own cookie jar then carries the session, so subsequent
    requests on the same client are authenticated as this user.
    """
    email = unique_email(prefix)
    await client.post(
        "/api/auth/register", json={"email": email, "password": VALID_PASSWORD}
    )
    await client.post(
        "/api/auth/login", json={"email": email, "password": VALID_PASSWORD}
    )
    return email


async def create(
    client: httpx.AsyncClient, name: str = "Acme QA", description: str | None = None
) -> httpx.Response:
    payload: dict[str, object] = {"name": name}
    if description is not None:
        payload["description"] = description
    return await client.post("/api/workspaces", json=payload)


# --- authentication -----------------------------------------------------------


async def test_unauthenticated_create_returns_401(test_database: TestDatabase) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        response = await create(client)

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


async def test_unauthenticated_list_returns_401(test_database: TestDatabase) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        response = await client.get("/api/workspaces")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHENTICATED"


# --- origin validation --------------------------------------------------------


@pytest.mark.parametrize(
    "origin_headers",
    [{"Origin": "http://evil.example.com"}, {}],
    ids=["untrusted_origin", "missing_origin"],
)
async def test_create_from_an_untrusted_origin_returns_403_and_creates_nothing(
    test_database: TestDatabase, origin_headers: dict[str, str]
) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        await sign_up_and_sign_in(client, "mallory")
        del client.headers["Origin"]
        response = await client.post(
            "/api/workspaces", json={"name": "Forged"}, headers=origin_headers
        )
        client.headers["Origin"] = TRUSTED_ORIGIN
        listed = await client.get("/api/workspaces")

    assert response.status_code == 403
    assert response.json()["error"]["code"] == "ORIGIN_NOT_ALLOWED"
    assert listed.json()["items"] == []


# --- successful creation ------------------------------------------------------


async def test_authenticated_create_returns_the_owner_membership(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        await sign_up_and_sign_in(client, "alice")
        response = await create(client, name="Acme QA", description="Core team")

    assert response.status_code == 201
    body = response.json()["data"]
    assert body["name"] == "Acme QA"
    assert body["description"] == "Core team"
    assert body["role"] == "owner"
    assert body["member_count"] == 1
    assert "id" in body and "created_at" in body


async def test_description_is_optional(test_database: TestDatabase) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        await sign_up_and_sign_in(client, "bob")
        response = await create(client, name="No description here")

    assert response.status_code == 201
    assert response.json()["data"]["description"] is None


async def test_created_workspace_appears_in_the_callers_list(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        await sign_up_and_sign_in(client, "carol")
        created = await create(client, name="Carol's Workspace")
        listed = await client.get("/api/workspaces")

    assert listed.status_code == 200
    items = listed.json()["items"]
    assert len(items) == 1
    assert items[0]["id"] == created.json()["data"]["id"]
    assert items[0]["role"] == "owner"
    assert items[0]["member_count"] == 1


async def test_listing_orders_newest_first(test_database: TestDatabase) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        await sign_up_and_sign_in(client, "dave")
        first = await create(client, name="First")
        second = await create(client, name="Second")
        listed = await client.get("/api/workspaces")

    ids = [item["id"] for item in listed.json()["items"]]
    assert ids == [second.json()["data"]["id"], first.json()["data"]["id"]]


# --- cross-user isolation ------------------------------------------------------


async def test_a_second_users_list_never_includes_the_first_users_workspace(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)

    async with running(app) as owner_client:
        await sign_up_and_sign_in(owner_client, "erin")
        owned = await create(owner_client, name="Erin's Workspace")

    async with running(app) as other_client:
        await sign_up_and_sign_in(other_client, "frank")
        other_list = await other_client.get("/api/workspaces")

    assert other_list.status_code == 200
    assert other_list.json()["items"] == []
    assert owned.status_code == 201


# --- validation -------------------------------------------------------------


async def test_empty_name_returns_422(test_database: TestDatabase) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        await sign_up_and_sign_in(client, "grace")
        response = await create(client, name="")

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_overlong_name_returns_422(test_database: TestDatabase) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        await sign_up_and_sign_in(client, "heidi")
        response = await create(client, name="x" * 201)

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


async def test_unexpected_fields_are_rejected(test_database: TestDatabase) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        await sign_up_and_sign_in(client, "ivan")
        response = await client.post(
            "/api/workspaces", json={"name": "Acme", "owner_id": str(uuid.uuid4())}
        )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
