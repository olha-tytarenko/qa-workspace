# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

QA Workspace: a full-stack app for managing product requirements and the QA process. Users create feature specs, analyze them with AI, review detected ambiguities/missing details, generate acceptance criteria and test cases, and track test coverage per requirement. AI-generated content is always a suggestion and must be reviewed/approved by a user. The project is at an early scaffold stage: the backend only exposes `GET /health`, `app/models/` is empty, there are no Alembic migrations yet, and the frontend is still the Vite template.

## Layout

Monorepo under `apps/`, orchestrated by `compose.yaml`:
- `apps/backend` — FastAPI + SQLAlchemy 2 + Alembic, Python >=3.13, managed with `uv`
- `apps/frontend` — React 19 + TypeScript + Vite (npm)
- `db` — Postgres 17 (compose only)

## Commands

Full stack (dev, hot reload for both apps; frontend :5173, backend :8000, Postgres :5432):
```
docker compose up --build
```

Backend (run from `apps/backend`; requires `DATABASE_URL`, e.g. `postgresql+psycopg://postgres:postgres@localhost:5432/qa_workspace`, via env or `.env`):
```
uv sync
uv run uvicorn app.main:app --reload
uv run alembic revision --autogenerate -m "message"
uv run alembic upgrade head
```

Frontend (run from `apps/frontend`):
```
npm run dev
npm run build      # tsc -b && vite build
npm run lint
```

No test framework is configured yet for either app.

## Architecture notes

- Config: `app/core/config.py` defines a pydantic-settings `Settings` singleton; `database_url` is required (no default), so importing it without `DATABASE_URL` set fails.
- DB: `app/db/session.py` creates the sync engine/`SessionLocal` (`autoflush=False`, `expire_on_commit=False`) and a `get_db` FastAPI dependency. Models must inherit `Base` from `app/db/base.py`.
- Alembic: `migrations/env.py` takes the URL from `settings.database_url` (not `alembic.ini`) and uses `Base.metadata` for autogenerate. New model modules must be imported somewhere Alembic loads (e.g. `app/models/__init__.py`, imported from `env.py`) or autogenerate will not see them — `env.py` currently imports no models.
- Compose mounts source into the containers and uses named volumes for `.venv` and `node_modules`, so dependencies are installed inside the image; after changing `pyproject.toml`/`package.json`, rebuild (`--build`) and, if stale, remove the volume.
- Frontend receives the API base URL as `VITE_API_URL` (`http://localhost:8000` in compose).