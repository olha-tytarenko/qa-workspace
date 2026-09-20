from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import get_settings
from app.db.session import create_engine, create_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Resolve settings through the override table so tests can replace them.
    # Missing or invalid configuration fails here, before the app serves traffic.
    settings = app.dependency_overrides.get(get_settings, get_settings)()

    engine = create_engine(settings)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)

    try:
        yield
    finally:
        await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="QA Workspace API", lifespan=lifespan)

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
