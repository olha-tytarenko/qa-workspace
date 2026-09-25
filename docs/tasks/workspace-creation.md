# Task: Workspace creation

## Goal

Let a logged-in user create a workspace and become its owner, per `docs/decisions.md` §1 ("Workspace creation is explicit") and §3 (roles held by a membership, never directly by a user).

## User-visible outcome

On `/workspaces`, a user sees their own workspaces (or a prompt to create one if they have none) and can open a "+ New workspace" modal to create one by name (required) and description (optional). The new workspace appears in the list immediately. An unauthenticated visitor is redirected to `/auth/sign-in`.

## Scope

- Backend: `POST /api/workspaces`, `GET /api/workspaces`, the `workspaces` and `workspace_memberships` tables, and a `get_current_user` dependency that resolves the session cookie — the first thing in the app that actually checks `Session.expires_at`.
- Frontend: the real `/workspaces` screen (list, empty state, create modal), replacing the placeholder.

## Explicit non-goals

`/api/auth/me`, logout, a reusable protected-route guard (see "Deviations" below), workspace editing or deletion, membership invitations, non-owner roles ever being assigned, projects, features, requirements, toast notifications.

## Relevant accepted decisions

`docs/decisions.md` §1 (workspace creation, roles), §3 (permission matrix baseline), §4 (API conventions — this task establishes the `{"items": [...]}` list envelope), §5 (SQLAlchemy/Alembic conventions).

## API or data-model impact

- New table `workspaces` (`id`, `name`, `description` nullable, `created_at`).
- New table `workspace_memberships` (`id`, `workspace_id` fk→`workspaces.id` cascade, `user_id` fk→`users.id` cascade, `role` checked to `owner`/`member`/`viewer`, `created_at`; unique on `(workspace_id, user_id)`).
- `POST /api/workspaces` → `201` with `{"data": {...}}`; `GET /api/workspaces` → `200` with `{"items": [...]}`. Both require authentication (`401 UNAUTHENTICATED` otherwise).

## Authorization rules

Any authenticated user may create a workspace (open creation, matching §1). `GET` only ever returns the caller's own memberships — never another user's workspaces, verified by a cross-user isolation test.

## Acceptance criteria

- An authenticated `POST` creates a workspace and an `owner` membership atomically; the response includes the caller's role and the workspace's member count (1).
- `GET` lists only the caller's workspaces, newest first.
- Unauthenticated requests to either endpoint return `401`.
- Validation: name required, ≤200 characters; description ≤2000 characters; unknown fields rejected.

## Deviations and decisions made during implementation

- **No `/api/auth/me`, no reusable route-guard component, no user identity in the header.** `WorkspacesPage`'s own list query requires auth; its `401` is what redirects to `/auth/sign-in`. The header shows only the brand — no avatar/name, since nothing fetches "who am I" in this slice. This was an explicit choice between two options (asked and answered) rather than an assumption; the fuller version (a reusable `RequireAuth` wrapper, `/api/auth/me`, a header identity chip) is the natural next step once a second protected screen actually needs it.
- **Workspace cards are not clickable.** Figma navigates to a per-workspace features screen (`/workspaces/{id}/features`) that doesn't exist and is out of scope — the same reasoning that dropped the sign-up success screen's "Go to my workspace" button rather than pointing it at a route that doesn't exist.
- **Feature count and "last activity" are dropped** from the card (no backing entity yet — features are deferred); **member count is kept** (real, from membership rows) and a **created-date is shown in its place** (also real). **Pending invitations are dropped** (invitations are deferred).
- **No toast notifications.** The modal closing and the new card appearing (via automatic query invalidation) is sufficient success feedback.
- **Role vocabulary is `owner`/`member`/`viewer`** per `docs/decisions.md`, not Figma's mock ("Editor").
- **`Brand`, `TextField`, and `ErrorBanner` were promoted from `features/auth/components/common/` to `src/components/`**, since workspaces now needs all three too — the exact trigger the frontend skill names for moving code into a shared module. `Brand` gained a `compact` variant for the workspaces top bar (Figma uses a visually distinct, smaller rendering there than on the auth pages). `AuthLayout` stayed in the auth `common/` folder, since it's still auth-specific.

## Required tests

- Backend integration: unauthenticated `401` on both endpoints; authenticated create returns the owner membership and `member_count: 1`; created workspace appears in the caller's list; listing orders newest-first; a second user's list never includes the first user's workspace (cross-workspace isolation); validation (empty/overlong name, extra fields). Schema tests for both tables' columns, constraints, and cascade-on-delete behavior. Unit tests for `get_current_user` (missing cookie, unknown token, expired session).
- Frontend: unauthenticated → redirected to sign-in; empty state; list renders cards; create flow (open → validate → submit → modal closes → new card appears); `Escape` closes the modal and returns focus to the trigger button; a server error shows a banner inside the modal without losing entered values.

## Required verification

All backend and frontend commands listed under "Commands" in `CLAUDE.md`.

## Assumptions and unresolved questions

None outstanding — the one genuine fork (auth/header scope) was resolved by explicit human decision before implementation.
