# QA Workspace backend

FastAPI service using async SQLAlchemy 2 (asyncpg) and PostgreSQL. Currently only `GET /health` exists.

## Configuration

`DATABASE_URL` is required and must use the async driver:

```
postgresql+asyncpg://postgres:postgres@localhost:5432/qa_workspace
```

Set it in the environment or in `apps/backend/.env`. Settings are validated at application startup and by Alembic, not at import time. Under `docker compose`, the URL is set in `compose.yaml`.

## Run

From this directory:

```
uv sync
uv run uvicorn app.main:app --reload
```

Or run the whole stack from the repository root with `docker compose up --build`.

## Verify

Run from this directory. Ruff and mypy are configured in `pyproject.toml` and cover `app`, `migrations` and `tests`.

```
uv run ruff format --check .   # format check, no changes
uv run ruff check .            # lint
uv run mypy                    # type check (strict)
uv run pytest                  # tests
```

Fix commands, which modify files:

```
uv run ruff format .           # apply formatting
uv run ruff check --fix .      # apply safe lint fixes only
```

The tests need no database or `DATABASE_URL`.

Type-checking limitation: mypy cannot see that pydantic-settings fills `database_url` from the environment, so `get_settings()` carries one narrow `# type: ignore[call-arg]`.

## Migrations

```
uv run alembic upgrade head
```

This needs a reachable PostgreSQL and `DATABASE_URL`. There are no models or migrations yet, so `upgrade head` is currently a no-op.
