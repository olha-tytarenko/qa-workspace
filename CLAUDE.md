# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

QA Workspace: a full-stack app for managing product requirements and the QA process. Users create feature specs, analyze them with AI, review detected ambiguities/missing details, generate acceptance criteria and test cases, and track test coverage per requirement. AI-generated content is always a suggestion and must be reviewed/approved by a user. Product rules and terminology live in `.claude/skills/qa-workspace-product-context/`.

## Current state

Early scaffold. No product features exist yet.

Implemented:
- Backend: FastAPI app with `GET /health`; async SQLAlchemy + asyncpg engine/session foundation; lazy settings; Alembic configured for the async engine; pytest tests for configuration and the app/session lifecycle; Ruff (format + lint) and strict mypy over `app`, `migrations`, `tests`.
- Frontend: unmodified Vite + React template.
- Docker Compose dev stack (frontend, backend, Postgres).

Not implemented (planned only — inspect the repo before assuming any of it exists):
- Domain models and Alembic migrations (`app/models/` is an empty package; `migrations/versions/` is empty)
- Authentication, authorization, workspace membership and isolation
- API endpoints beyond `/health`, frontend routes, API client, router
- Redis, task queue/workers, SSE, AI provider integration
- Frontend test runner, end-to-end tests, CI configuration

## Layout

Monorepo under `apps/`, orchestrated by `compose.yaml`:
- `apps/backend` — FastAPI + async SQLAlchemy 2 (asyncpg) + Alembic, Python >=3.13, managed with `uv`
- `apps/frontend` — React 19 + TypeScript + Vite (npm)
- `db` — Postgres 17 (compose only)

## Commands

Full stack (dev, hot reload for both apps; frontend :5173, backend :8000, Postgres :5432):
```
docker compose up --build
```

Backend (run from `apps/backend`; requires `DATABASE_URL` using the async driver, e.g. `postgresql+asyncpg://postgres:postgres@localhost:5432/qa_workspace`, via env or `.env`):
```
uv sync
uv run uvicorn app.main:app --reload
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head
```

Backend verification (from `apps/backend`; all four must pass, none needs a database):
```
uv run ruff format --check .   # format check
uv run ruff check .            # lint
uv run mypy                    # type check (strict, no plugins)
uv run pytest                  # tests
```
To fix: `uv run ruff format .` and `uv run ruff check --fix .` (safe fixes only). Do not add blanket ignores; a `# type: ignore` needs a specific error code and a reason (see `get_settings()`).

Frontend (run from `apps/frontend`):
```
npm run dev
npm run build      # tsc -b && vite build (also the only type-check)
npm run lint
```

Testing status: backend has pytest (`apps/backend/tests`); the frontend has no test runner. Frontend `npm run build` is its only type-check.

## Architecture notes

- Config: `app/core/config.py` exposes `get_settings()` (cached, pydantic-settings). Nothing is read at import time. `database_url` is required and must start with `postgresql+asyncpg://`. The app validates settings in its lifespan at startup; tests override it with `app.dependency_overrides[get_settings]`.
- DB: async only. `app/main.py` lifespan creates the `AsyncEngine` and `async_sessionmaker` (`autoflush=False`, `expire_on_commit=False`) on `app.state` and disposes the engine on shutdown. `get_session` in `app/db/session.py` yields one `AsyncSession` per request and never commits implicitly; use cases open explicit transactions (`async with session.begin()`). Never make blocking DB calls in `async def` code. Models must inherit `Base` from `app/db/base.py`.
- Alembic: `migrations/env.py` uses the async engine with the URL from `get_settings()` (not `alembic.ini`) and `Base.metadata` for autogenerate. New model modules must be imported somewhere Alembic loads (e.g. `app/models/__init__.py`, imported from `env.py`) or autogenerate will not see them — `env.py` currently imports no models.
- Compose mounts source into the containers and uses named volumes for `.venv` and `node_modules`, so dependencies are installed inside the image; after changing `pyproject.toml`/`package.json`, rebuild (`--build`) and, if stale, remove the volume.
- Frontend receives the API base URL as `VITE_API_URL` (`http://localhost:8000` in compose); nothing reads it yet.
