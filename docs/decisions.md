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
- Workspace creation is explicit. **Implemented**: `POST /api/workspaces` creates a workspace and an `owner` membership for the caller in one transaction (see §8).
- Requirements are created manually. Importing requirements is deferred, not MVP functionality. A requirement may have an optional type (its allowed values are not yet defined).
- Open user registration is allowed in the MVP. Email verification is deferred.

## 2. Sessions and security

**Accepted.** Password hashing, CORS, and sessions/cookies are implemented as of the registration and login slices (see §8); origin validation for cookie-authenticated mutating requests is implemented as of the logout slice.

- Session tokens are opaque random values. Only a cryptographic hash of each token is stored in the database. **Implemented**: a `secrets.token_urlsafe(32)` token, SHA-256-hashed at rest (`app/core/security.py`) — deliberately not Argon2id, since the token's own entropy makes a fast deterministic hash correct here, unlike passwords.
- Session cookie: `HttpOnly`, `SameSite=Lax`, `Secure` in production. **Implemented**: `Secure` is controlled by the `session_cookie_secure` setting (`false` by default for local HTTP development).
- Session TTL: 14 days. **Implemented** as a fixed constant (`SESSION_TTL`), not per-environment configuration.
- Mutating cookie-authenticated requests must validate the request `Origin`. **Implemented** by `require_trusted_origin` (`app/api/dependencies.py`): the request `Origin` must be present and in the CORS allowlist (`cors_allowed_origins`), or the request gets `403 ORIGIN_NOT_ALLOWED`. It guards `POST /api/auth/logout` and `POST /api/workspaces`, and every future mutation authenticated by the session cookie must add it. `POST /api/auth/login` and `/register` do not use it, because they are not authenticated by an existing session.
- Password hashing uses Argon2id through `argon2-cffi`. **Implemented.**
- A request for a workspace resource by a non-member returns `404`, not `403`, so resource existence is not leaked. `403` is only for a member who lacks the role required for an action.
- CORS: the first product API slice must configure FastAPI CORS with an explicit frontend-origin allowlist supplied through configuration. Local development allows the configured Vite origin. Credentialed requests are enabled, so wildcard origins must never be used. Production origins come from environment-specific configuration and are never hard-coded. **Implemented.** CORS begins with the first *browser-consumed* product API slice, not specifically the first cookie-authenticated one: the Vite dev server and backend are different origins regardless of whether the slice uses cookies, so a browser cannot call the API cross-origin without it. Cookie-specific security behavior (the `HttpOnly`/`SameSite`/`Secure` cookie itself, and `Origin` validation on authenticated mutating requests) begins with the first cookie-authenticated slice; both are now implemented.

## 3. Permission matrix

**Accepted** baseline. Only the owner-creates-workspace path is implemented so far (`POST /api/workspaces` always creates the caller as `owner` — see §8); every other cell (member/viewer actions, role changes, deletion) has no endpoint yet. Detailed membership-management UX and invitation flows are deferred.

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
- Successful single-resource responses use a fixed envelope with a top-level `data` property, established by the registration endpoint:

  ```json
  { "data": { "id": "...", "...": "..." } }
  ```

  List responses use a top-level `items` array, established by `GET /api/workspaces`:

  ```json
  { "items": [ { "id": "...", "...": "..." } ] }
  ```

  No pagination or cursor fields yet — a user's own workspace count is small and unbounded pagination isn't warranted until a real endpoint needs it.

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
- `/` is the start screen: it redirects to `/workspaces`, which shows the workspace list or, on its own `401`, redirects to `/auth/sign-in` (see §8). The Vite template screen has been removed.

## 8. Current implementation

Verified in the repository:

- Backend: FastAPI with `GET /health`; `POST /api/auth/register`; `POST /api/auth/login` (credential verification, session creation, the `HttpOnly`/`SameSite=Lax` session cookie); `POST /api/auth/logout` (`204`; deletes only the current session row and clears the cookie; idempotent, so a missing, unknown or expired cookie also gets `204`); `POST /api/workspaces` and `GET /api/workspaces` (create, and list the caller's own workspaces with their role and member count), both behind `get_current_user` (`app/api/dependencies.py` — resolves the session cookie, the first code that checks `Session.expires_at`); the `users`, `sessions`, `workspaces`, and `workspace_memberships` tables and their migrations; CORS middleware with a configurable origin allowlist; `Origin` validation on cookie-authenticated mutations (§2); async SQLAlchemy engine and session foundation; lazy settings; the PostgreSQL test foundation described above.
- Frontend: `/` as the start screen (redirects to `/workspaces`, so a signed-in user sees the workspace list and a signed-out visitor ends up at sign-in), the `/auth/sign-up` screen, the `/auth/sign-in` screen (redirects to `/workspaces` on success), and `/workspaces` — a real screen listing the caller's workspaces (or an empty-state prompt) with a "+ New workspace" modal (name, optional description) and a "Sign out" button in the header (on success it clears the TanStack Query cache and goes to `/auth/sign-in`; on failure it shows an inline error and stays signed in). An unauthenticated visitor is redirected to `/auth/sign-in` by the list request's own `401`; there is no separate `/api/auth/me` or reusable route-guard yet (see §9).
- Docker Compose dev stack: frontend, backend, Postgres.

## 9. Deferred

Not built, and not to be introduced without an explicit, scoped task:

- `/api/auth/me`, signing out of all sessions, a reusable protected-route guard (each screen currently derives "not authenticated" from its own request's `401` rather than a shared primitive), memberships beyond the creator's own `owner` row, invitation flows, workspace editing/deletion, projects, features, requirements, and every API beyond `/health`, `/api/auth/register`, `/api/auth/login`, `/api/auth/logout`, and `/api/workspaces`. (Users, registration, login, logout, and workspace creation are implemented — see §8.)
- Email verification, password reset, "remember me" / variable session length, requirement import.
- Follow-up considerations, not readiness blockers: API-client normalization of network failures and non-JSON successful responses; restricting the test database by host; a test that detects a forgotten model import; mutation-testing the database fixtures; parallel test-database provisioning.
- AI generation, imports, Redis, Celery or any task queue, workers, SSE.
- Playwright, CI/CD, seeded application users, logging and observability infrastructure, request-ID middleware (the current per-error `uuid4` in `app/core/errors.py` is a documented stand-in, not that infrastructure).
