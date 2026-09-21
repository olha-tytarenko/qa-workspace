# Decisions

Accepted architecture and product decisions for QA Workspace. When something here conflicts with code, docs or skills, this file wins over them (see the authority order in `CLAUDE.md`), and the conflict must be reported, not silently resolved.

Every section is labelled:

- **Accepted**: a decision. Implement later work consistently with it.
- **Implemented**: exists in the repository today and was verified.
- **Deferred**: not built and not to be built without an explicit, scoped task.

Changing an accepted decision needs an explicit human decision. Record the change here.

## 1. Product and domain

**Accepted**

- Authentication uses email and password. Authentication state uses server-managed sessions in HttpOnly cookies.
- Hierarchy: Workspace → Project → Feature → Requirement. Project remains part of the domain; project functionality is not part of the first product slice.
- Workspace roles are `owner`, `member`, `viewer`. A role belongs to a workspace membership, never directly to a user. A user may own or belong to multiple workspaces.
- Workspace creation is explicit.
- Requirements are created manually. Importing requirements is deferred, not MVP functionality. A requirement may have an optional type (its allowed values are not yet defined).
- Open user registration is allowed in the MVP. Email verification is deferred.

## 2. Sessions and security

**Accepted** (none of this is implemented yet)

- Session tokens are opaque random values. Only a cryptographic hash of each token is stored in the database.
- Session cookie: `HttpOnly`, `SameSite=Lax`, `Secure` in production.
- Session TTL: 14 days.
- Mutating cookie-authenticated requests must validate the request `Origin`.
- Password hashing uses Argon2id through `argon2-cffi`.
- A request for a workspace resource by a non-member returns `404`, not `403`, so resource existence is not leaked. `403` is only for a member who lacks the role required for an action.
- CORS: the first product API slice must configure FastAPI CORS with an explicit frontend-origin allowlist supplied through configuration. Local development allows the configured Vite origin. Credentialed requests are enabled, so wildcard origins must never be used. Production origins come from environment-specific configuration and are never hard-coded. The middleware is implemented and tested together with the first cookie-authenticated API slice; it does not exist yet, and the frontend API client (`credentials: 'include'`) cannot work cross-origin in a browser until it does.

## 3. Permission matrix

**Accepted** baseline, not yet implemented. Detailed membership-management UX and invitation flows are deferred.

| Capability | `owner` | `member` | `viewer` |
|---|---|---|---|
| Read the workspace and its content | yes | yes | yes |
| Modify the workspace | yes | no | no |
| Manage memberships and roles | yes | no | no |
| Create, update, delete product and QA artifacts | yes | yes | no |
| Review and approve AI-generated suggestions | yes | yes | no |
| Delete the workspace | yes | no | no |

Additional rules:

- Only an owner may delete a workspace.
- The last owner cannot leave, be removed, or be demoted.
- `viewer` cannot create, modify, delete or approve anything, and cannot manage members.

## 4. API conventions

**Accepted**

- Product API endpoints are served under the `/api` prefix.
- `GET /health` is an unprefixed infrastructure probe and is the explicit exception. It must not be moved or duplicated under `/api` merely to satisfy the product API convention.
- Persisted entity primary keys are UUIDv4. This applies to entities, not to every identifier: request IDs and other correlation identifiers do not need to be UUIDv4.
- Ordinary RESTful routes for CRUD. `:action` routes only for genuine domain commands that do not map to CRUD (for example `POST /api/requirements/{id}:approve`).
- Errors use one fixed envelope, illustrated in `qa-workspace-backend-api-patterns` (the shape is fixed; the values are examples):

  ```json
  { "error": { "code": "...", "message": "...", "details": {}, "request_id": "..." } }
  ```

  Clients branch on `code`, never on `message`. `request_id` is a correlation identifier.

## 5. SQLAlchemy, Alembic and transactions

**Implemented** in `apps/backend/app/db/base.py`, `app/models/__init__.py` and `migrations/env.py`:

- Constraint and index names follow a fixed naming convention (`NAMING_CONVENTION`): `pk_`, `fk_`, `uq_`, `ck_`, `ix_` prefixes with the table and every participating column (for example `uq_membership_user_id_workspace_id`), so composite constraints that share a first column cannot collide. SQLAlchemy truncates generated names longer than PostgreSQL's 63 characters deterministically.
- **Check constraints must be named explicitly** (`CheckConstraint(..., name="...")`), because the name is part of the generated `ck_` name. An unnamed check constraint raises an error.
- Primary keys use `uuid_pk()`: a `uuid.uuid4` default generated in Python. There is deliberately no PostgreSQL `gen_random_uuid()` server default.
- Every `Mapped[datetime]` is `timestamptz`. Application code stores and reads timezone-aware UTC values.
- Model modules are imported in `app/models/__init__.py` and nowhere else. `migrations/env.py` imports that package, so Alembic autogenerate and `alembic check` see every model.
- Async SQLAlchemy only. Request handlers and services control commits explicitly (`async with session.begin()`). The `get_session` dependency never commits implicitly.

**Not implemented:** timestamp mixins or `created_at`/`updated_at` columns, base entity classes, repositories. They arrive with the first model, only if it needs them.

## 6. Testing

**Implemented**

- Backend integration tests use PostgreSQL, never SQLite.
- Tests use a separate `qa_workspace_test` database, named by `TEST_DATABASE_URL` (set by `compose.yaml`). The name must end in `_test` and must differ from `DATABASE_URL`, or the suite refuses to run. Tests never connect to the development database.
- One coordinated session lifecycle (the `test_database` fixture): validate the URL, drop and recreate the test database once, run `alembic upgrade head` from empty, then run tests. Individual tests never drop or recreate the database.
- Per-test isolation: each test gets a session inside an outer transaction that is rolled back (savepoints, so a `commit()` in the code under test is also discarded). Engines and connections are closed after each use.
- Database tests fail, rather than skip, when `TEST_DATABASE_URL` is unset. Run them through Docker Compose.
- Frontend: Vitest, React Testing Library, `user-event`, `jest-dom`, MSW. Unhandled requests are rejected and logged as errors (`onUnhandledRequest: 'error'`); this does not by itself fail a test if the code under test swallows the failed request.
- **Concurrency:** only one backend integration-test session may use the shared `qa_workspace_test` database at a time. The lifecycle drops and recreates that database, so it is not safe for concurrent pytest processes or `pytest-xdist` (two simultaneous runs were observed to collide). Parallel execution must not be enabled until the test infrastructure provisions a unique database per worker or session.
- Canonical commands run through Docker Compose (see `CLAUDE.md`).

**Accepted, not yet built:** test data factories are plain `async def create_<entity>(session, **overrides)` helpers, added with the first model. Playwright E2E is deferred.

## 7. Frontend foundation

**Implemented**

- Dependencies: TanStack Query, `react-router-dom`, React Hook Form, Zod (installed, unused until the first real form), Vitest and the testing libraries above.
- Composition points: `src/app/AppProviders.tsx`, `src/app/router.tsx`, `src/app/queryClient.ts`.
- API client convention: `src/lib/api/client.ts` (`apiRequest`, `ApiError`). It reads `VITE_API_URL` on use, prefixes `/api`, always sends cookies, and turns non-2xx responses into `ApiError` from the error envelope.
- The only route renders the unmodified Vite template screen. There are no product screens.

## 8. Current implementation

Verified in the repository:

- Backend: FastAPI with `GET /health` only; async SQLAlchemy engine and session foundation; lazy settings; Alembic on the async engine (no models, no migrations); the PostgreSQL test foundation described above.
- Frontend: the Vite template with the foundation from section 7.
- Docker Compose dev stack: frontend, backend, Postgres.

## 9. Deferred

Not built, and not to be introduced without an explicit, scoped task:

- Users, sessions, registration, login, workspaces, memberships, projects, features, requirements, and every API beyond `/health`.
- Invitation flows, email verification, password reset, requirement import.
- CORS middleware (the decision is recorded in section 2; the implementation arrives with the first cookie-authenticated API slice).
- Follow-up considerations, not readiness blockers: API-client normalization of network failures and non-JSON successful responses; restricting the test database by host; a test that detects a forgotten model import; mutation-testing the database fixtures; parallel test-database provisioning; backend implementation of the error envelope and `request_id`.
- AI generation, imports, Redis, Celery or any task queue, workers, SSE.
- Playwright, CI/CD, seeded application users, logging and observability infrastructure, request-ID middleware.
