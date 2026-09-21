# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

QA Workspace: a full-stack app for managing product requirements and the QA process. Users create feature specs, analyze them with AI, review detected ambiguities/missing details, generate acceptance criteria and test cases, and track test coverage per requirement. AI-generated content is always a suggestion and must be reviewed/approved by a user. Product rules and terminology live in `.claude/skills/qa-workspace-product-context/`. Accepted architecture and product decisions live in `docs/decisions.md`.

## Authority order

When instructions conflict, follow the higher item and **report the conflict** instead of silently picking one:

1. The current, explicitly approved task.
2. Accepted decision records (`docs/decisions.md`).
3. Product and domain documentation (`.claude/skills/qa-workspace-product-context/`).
4. Repository-specific skills (`.claude/skills/`).
5. General repository documentation (READMEs, this file's descriptive sections).
6. Existing code patterns.

Existing code is evidence of current behavior. It never silently overrides an accepted decision. Documentation describes only what was verified; planned work is labelled as planned.

## Workflow

Every task follows this sequence. Do not skip steps.

1. **Investigate** the relevant repository state. Cross-check docs against code.
2. **Plan**: a concrete file-by-file plan, conflicts found, commands to run, commands needing approval, open risks.
3. **Wait for explicit human approval** of the plan. No edits before it.
4. **Implement only the approved plan.** No unrelated refactoring.
5. **Add or update tests** for the behavior.
6. **Verify**: run every applicable command below.
7. **Report** using the format below.

Never commit or push unless explicitly instructed. Never delete or reset Docker volumes or development data without explicit approval naming the exact volume and command.

### Stop and ask

Stop and ask the human when a product, security, data, or architecture decision is genuinely missing, or when the work would require an unapproved dependency, a major-version upgrade, planned-but-absent infrastructure (Redis, queues, workers, SSE, AI provider), or a destructive operation. Do not invent the decision. Continue with unaffected work.

## Skills: when to invoke

Invoke the skill before working in its area. Skills own the detailed rules; do not restate them here. The frontend skill was renamed to `qa-workspace-frontend-patterns` (directory, frontmatter and references now agree); start a new Claude Code session to guarantee it is discovered under the new name.

| Skill | Invoke when |
|---|---|
| `qa-workspace-implement-feature` | Implementing or changing user-visible behavior end to end. |
| `qa-workspace-product-context` | Product judgment, terminology, workflow, review/approval semantics, traceability. |
| `qa-workspace-evolve-domain-model` | Adding or changing entities, ownership, lifecycle states, invariants, or persisted meaning. |
| `qa-workspace-backend-api-patterns` | Endpoints, schemas, services, transactions, authorization, error contracts, migrations. |
| `qa-workspace-frontend-patterns` | React components, routes, forms, client/server state, API integration. |
| `qa-workspace-testing` | Adding or changing any automated test or test infrastructure. |
| `qa-workspace-code-review` | Reviewing a diff, PR, or implementation. Reports findings; does not fix. |
| `qa-workspace-ai-generation` | Analysis, generation, prompts, structured AI output, provenance (none exists yet). |

## Definition of Done

A task is done only when all of these hold:

- The approved acceptance criteria are met and nothing outside the approved scope changed.
- Tests cover the new or changed behavior, and you confirmed they can fail when the behavior is wrong.
- Every applicable verification command below was actually run and passed. Nothing is reported as passing unless it ran successfully.
- Docs and `docs/decisions.md` match the code (implemented vs planned stays accurate).
- The diff was inspected for unintended files, secrets, debug code, and unrelated formatting.
- Nothing was committed or pushed.

## Completion report format

End every task with these sections, in this order:

1. **Files changed and why.**
2. **Dependencies added or changed.**
3. **Decisions persisted.**
4. **Tests added.**
5. **Verification run**: every command and its actual result.
6. **Not run**, with the exact reason.
7. **Assumptions made.**
8. **Remaining risks or follow-up.**
9. **Confirmation** that no commit, push, destructive operation, or out-of-scope functionality happened.

## Current state

Early scaffold. No product features exist yet. Accepted decisions for the first product slices are in `docs/decisions.md` and are **not implemented**.

Implemented:
- Backend: FastAPI app with `GET /health`; async SQLAlchemy + asyncpg engine/session foundation; lazy settings; Alembic configured for the async engine with model discovery via `app/models`; SQLAlchemy conventions (constraint naming, `uuid_pk()`, timezone-aware datetimes) in `app/db/base.py`; PostgreSQL test foundation (separate `qa_workspace_test` database, migrations applied once per session, rolled-back per-test sessions); Ruff (format + lint) and strict mypy over `app`, `migrations`, `tests`.
- Frontend: Vite + React with the approved foundation (TanStack Query, `react-router-dom`, React Hook Form, Zod, Vitest, React Testing Library, MSW); provider/route composition and a minimal API client. The only screen is still the Vite template.
- Docker Compose dev stack (frontend, backend, Postgres).

Not implemented (planned only — inspect the repo before assuming any of it exists):
- Domain models and Alembic migrations (`app/models/` has no models; `migrations/versions/` has no migrations)
- Authentication, authorization, workspace membership and isolation
- API endpoints beyond `/health`, product screens, application routes
- Redis, task queue/workers, SSE, AI provider integration
- Playwright/end-to-end tests, CI configuration

## Layout

Monorepo under `apps/`, orchestrated by `compose.yaml`:
- `apps/backend` — FastAPI + async SQLAlchemy 2 (asyncpg) + Alembic, Python >=3.13, managed with `uv`
- `apps/frontend` — React 19 + TypeScript + Vite (npm)
- `db` — Postgres 17 (compose only)
- `docs/` — `decisions.md` (accepted decisions), `tasks/_template.md` (task specification template)

## Commands

**Docker Compose is the canonical way to run everything.** Do not rely on host-installed `uv`/`node`. Start the stack (frontend :5173, backend :8000, Postgres :5432):
```
docker compose up --build
```

Backend verification — all must pass; database tests use the `qa_workspace_test` database that `compose.yaml` configures:
```
docker compose exec -T backend uv run --no-sync ruff format --check .   # format check
docker compose exec -T backend uv run --no-sync ruff check .            # lint
docker compose exec -T backend uv run --no-sync mypy                    # type check (strict, no plugins)
docker compose exec -T backend uv run --no-sync pytest                  # unit + PostgreSQL integration tests, incl. migration checks
docker compose exec -T backend uv run --no-sync alembic heads           # lists migration heads (does not connect to a database)
```
The migration check ("database is at head" and `alembic check` for model drift) runs inside pytest against the **test** database. Do not run `alembic check` or `alembic current` directly: they connect to the development database (`DATABASE_URL`) and can create its `alembic_version` table, so they need approval like any command that touches it.
To fix formatting/lint (modifies files): `... ruff format .` and `... ruff check --fix .` (safe fixes only). Do not add blanket ignores; a `# type: ignore` or `# noqa` needs a specific code and a reason.

Frontend verification — all must pass:
```
docker compose exec -T frontend npm run lint
docker compose exec -T frontend npm run typecheck   # tsc -b
docker compose exec -T frontend npm run test        # vitest run
docker compose exec -T frontend npm run build       # tsc -b && vite build
```

Migrations (need approval — they change a database): `docker compose exec backend uv run --no-sync alembic revision --autogenerate -m "message"` and `... alembic upgrade head`. Review every generated migration by hand. Never run `alembic downgrade`.

Stale tools: the compose named volumes (`backend_venv`, `frontend_node_modules`) mask dependencies baked into the image. If a tool is missing, run `docker compose exec backend uv sync --frozen` (or `npm ci` in the frontend); this needs approval. Do not remove the volume.

Testing status: backend pytest in `apps/backend/tests` (unit tests need no database; `tests/integration` needs PostgreSQL). Frontend Vitest specs sit beside the code. There are no end-to-end tests.

Test concurrency: **run only one backend integration-test session at a time.** The shared `qa_workspace_test` database is dropped and recreated at the start of each session, so the current lifecycle is not safe for concurrent pytest processes or `pytest-xdist` (two simultaneous runs collide). Do not enable parallel execution until the test infrastructure provisions a unique database per worker or session.

## Architecture notes

- Config: `app/core/config.py` exposes `get_settings()` (cached, pydantic-settings). Nothing is read at import time. `database_url` is required and must start with `postgresql+asyncpg://`. The app validates settings in its lifespan at startup; tests override it with `app.dependency_overrides[get_settings]`.
- DB: async only. `app/main.py` lifespan creates the `AsyncEngine` and `async_sessionmaker` (`autoflush=False`, `expire_on_commit=False`) on `app.state` and disposes the engine on shutdown. `get_session` in `app/db/session.py` yields one `AsyncSession` per request and never commits implicitly; use cases open explicit transactions (`async with session.begin()`). Never make blocking DB calls in `async def` code. Models must inherit `Base` from `app/db/base.py`, use `uuid_pk()` for primary keys, and follow the naming and timestamp conventions in `docs/decisions.md`.
- Alembic: `migrations/env.py` uses the async engine with the URL from `get_settings()` (or an explicit `Config.attributes["database_url"]`, which the tests use for the test database) and `Base.metadata` for autogenerate. New model modules must be imported in `app/models/__init__.py`, which `env.py` imports, or autogenerate will not see them.
- Test database: never point a test at the development database. `tests/database.py` refuses any `TEST_DATABASE_URL` whose database name does not end in `_test` or that equals `DATABASE_URL`. Only the `test_database` fixture may drop or create the test database. Use the `db_session` fixture for database tests.
- Frontend API access: go through `src/lib/api/client.ts` (`apiRequest`). Base URL comes from `VITE_API_URL` (`http://localhost:8000` in compose), paths are under `/api` (the unprefixed `GET /health` probe is the one exception).
- Environment files: real `.env` files are git-ignored; only `.env.example` files are tracked. Never read, print, or copy a real `.env`, and never print a database URL containing a password.

## Safety boundaries

`.claude/settings.json` pre-approves the non-destructive verification commands above. Note that `pytest` intentionally drops and recreates the guarded `qa_workspace_test` database, and only that one. The rules also:

- require approval for installs, container recreation, migrations, git writes, and arbitrary `psql` through Docker Compose;
- deny destructive operations: recursive deletes, `docker compose down -v`, volume deletion, `dropdb` and `alembic downgrade` through Docker Compose, force-push, `git reset --hard`, and similar.

These rules are guardrails, not a security boundary: command patterns can be sidestepped (for example by different spelling, a wrapped shell, or SQL typed inside `psql`). They deliberately do not block ordinary code search or diagnostics. Do not attempt to work around a denial. Ask.

Also, regardless of what the rules block: do not print environment variables wholesale, do not run `docker compose config` or `docker inspect` without need (they can expose secrets), and do not touch the `postgres_data` volume.
