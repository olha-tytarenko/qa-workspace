from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import httpx
import pytest
from fastapi import FastAPI

from app.core.config import Settings, get_settings
from app.main import create_app
from tests.database import TestDatabase

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

ALLOWED_ORIGIN = "http://localhost:5173"
DISALLOWED_ORIGIN = "http://evil.example.com"


def app_for(test_database: TestDatabase) -> FastAPI:
    app = create_app()
    app.dependency_overrides[get_settings] = lambda: Settings(
        database_url=test_database.url.render_as_string(hide_password=False),
        cors_allowed_origins=ALLOWED_ORIGIN,
    )
    return app


@asynccontextmanager
async def running(app: FastAPI) -> AsyncIterator[httpx.AsyncClient]:
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(
            transport=transport, base_url="http://test"
        ) as client:
            yield client


async def test_allowed_origin_receives_credentialed_cors_headers(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        response = await client.options(
            "/api/auth/register",
            headers={
                "Origin": ALLOWED_ORIGIN,
                "Access-Control-Request-Method": "POST",
            },
        )

    assert response.headers["access-control-allow-origin"] == ALLOWED_ORIGIN
    assert response.headers["access-control-allow-credentials"] == "true"


async def test_unapproved_origin_does_not_receive_cors_headers(
    test_database: TestDatabase,
) -> None:
    app = app_for(test_database)

    async with running(app) as client:
        response = await client.options(
            "/api/auth/register",
            headers={
                "Origin": DISALLOWED_ORIGIN,
                "Access-Control-Request-Method": "POST",
            },
        )

    assert "access-control-allow-origin" not in response.headers
