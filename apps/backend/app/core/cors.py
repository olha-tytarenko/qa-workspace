from fastapi.middleware.cors import CORSMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send


class LazyCORSMiddleware:
    """Defers the allowed-origins list to settings resolved during `lifespan`.

    `CORSMiddleware` needs its origins at construction time, but this app
    deliberately resolves settings only inside `lifespan` (see
    `app/core/config.py`), which itself runs after Starlette's middleware
    stack has already been built. This wraps the real `CORSMiddleware` and
    builds it lazily, on the first non-lifespan call, reading
    `app.state.cors_origins` (set by `lifespan` before it yields). If that
    state was never set (the app was used without running its lifespan, as
    some tests do), it falls back to an empty origin list rather than
    raising, so unrelated behavior downstream is unaffected.
    """

    def __init__(self, app: ASGIApp) -> None:
        self.app = app
        self._inner: ASGIApp | None = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        if self._inner is None:
            origins = getattr(scope["app"].state, "cors_origins", [])
            self._inner = CORSMiddleware(
                self.app,
                allow_origins=origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        await self._inner(scope, receive, send)
