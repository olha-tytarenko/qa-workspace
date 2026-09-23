from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.core.config import get_settings
from app.core.cors import LazyCORSMiddleware
from app.core.errors import register_exception_handlers
from app.db.session import create_engine, create_session_factory


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Resolve settings through the override table so tests can replace them.
    # Missing or invalid configuration fails here, before the app serves traffic.
    settings = app.dependency_overrides.get(get_settings, get_settings)()

    engine = create_engine(settings)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.cors_origins = settings.cors_origins

    try:
        yield
    finally:
        await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(title="QA Workspace API", lifespan=lifespan)
    app.add_middleware(LazyCORSMiddleware)
    register_exception_handlers(app)
    app.include_router(auth_router, prefix="/api/auth", tags=["auth"])

    @app.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
