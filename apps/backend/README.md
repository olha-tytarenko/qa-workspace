# QA Workspace backend

FastAPI service using async SQLAlchemy 2 (asyncpg) and PostgreSQL. Currently only `GET /health` exists. Accepted decisions for what comes next are in `docs/decisions.md`.

## Configuration

Run through Docker Compose from the repository root; `compose.yaml` sets the variables. `apps/backend/.env.example` documents them:

- `DATABASE_URL` is required and must use the async driver: `postgresql+asyncpg://postgres:postgres@db:5432/qa_workspace`.
- `TEST_DATABASE_URL` names the test database (`qa_workspace_test`). Its database name must end in `_test` and differ from `DATABASE_URL`.

Settings are validated at application startup and by Alembic, not at import time. Real `.env` files are git-ignored.

## Run

From the repository root: `docker compose up --build`.

## Verify

From the repository root (Docker Compose is the canonical path; Ruff and mypy are configured in `pyproject.toml` and cover `app`, `migrations` and `tests`):

```
docker compose exec -T backend uv run --no-sync ruff format --check .   # format check, no changes
docker compose exec -T backend uv run --no-sync ruff check .            # lint
docker compose exec -T backend uv run --no-sync mypy                    # type check (strict)
docker compose exec -T backend uv run --no-sync pytest                  # tests, incl. migration checks
docker compose exec -T backend uv run --no-sync alembic heads           # migration heads (no database connection)
```

The migration check (database at head, and `alembic check` for model drift) runs inside pytest against the test database. Running `alembic check` or `alembic current` directly connects to the development database, so they need approval.

Fix commands, which modify files: `... ruff format .` and `... ruff check --fix .` (safe fixes only).

If Ruff or mypy is missing, the `backend_venv` volume is stale: run `docker compose exec backend uv sync --frozen`.

## Tests

- Unit tests need no database.
- `tests/integration` uses the real PostgreSQL test database. The `test_database` fixture (`tests/conftest.py`) recreates `qa_workspace_test` once per session, runs `alembic upgrade head` on it, and only then do tests run. Each test's `db_session` is rolled back afterwards, and tests never touch `qa_workspace`. Without `TEST_DATABASE_URL` these tests fail (they do not skip). Run only one integration-test session at a time: the shared test database is recreated per session, so concurrent pytest processes or `pytest-xdist` are not supported.

Type-checking limitation: mypy cannot see that pydantic-settings fills `database_url` from the environment, so `get_settings()` carries one narrow `# type: ignore[call-arg]`.

## Migrations

```
docker compose exec backend uv run --no-sync alembic upgrade head
```

Needs approval, because it changes a database. There are no models or migrations yet, so `upgrade head` is currently a no-op. New model modules must be imported in `app/models/__init__.py`. Conventions (naming, UUID keys, timestamps) are in `app/db/base.py` and `docs/decisions.md`.
