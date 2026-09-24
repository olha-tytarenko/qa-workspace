# Task: Login

## Goal

Let an existing user sign in with their email and password, establishing a server-managed session, per `docs/decisions.md` §1.

## User-visible outcome

A user can open `/auth/sign-in`, submit their email and password, and land on `/workspaces` on success. Validation and error states (missing fields, incorrect credentials, server error) are shown inline or via a banner without losing entered values.

## Scope

- Backend: `POST /api/auth/login`, the `sessions` table, opaque session tokens hashed at rest, the `HttpOnly`/`SameSite=Lax` session cookie.
- Frontend: the `/auth/sign-in` screen (form, validation, error states, redirect on success) and the `/workspaces` route as an empty placeholder.

## Explicit non-goals

Logout, `/api/auth/me`, protected-route guards, real workspace functionality (list, create, data model, API), password reset, "remember me" / variable session length, rate limiting, CSRF/`Origin` validation (still deferred per `docs/decisions.md` §2 until a cookie-authenticated *mutating* endpoint exists — login itself creates the session rather than using one).

## Relevant accepted decisions

`docs/decisions.md` §1 (email+password auth, server-managed sessions in `HttpOnly` cookies), §2 (opaque session tokens hashed at rest, `HttpOnly`/`SameSite=Lax`/`Secure`-in-production cookie, 14-day TTL), §4 (API conventions), §5 (SQLAlchemy/Alembic conventions). This task flips §2's and §8's "not implemented" framing for sessions/cookies to implemented.

## API or data-model impact

- New table `sessions` (`id` uuid pk, `user_id` fk → `users.id` `ON DELETE CASCADE`, `token_hash` unique, `created_at`, `expires_at`), one new Alembic migration.
- New endpoint `POST /api/auth/login` → `200` with `{"data": {"id", "email", "created_at"}}` and a `Set-Cookie: session=...` header, or the fixed error envelope (`422` validation, `401` invalid credentials, `500` unexpected).

## Authorization rules

None — the login endpoint itself is unauthenticated by nature. `/workspaces` is deliberately left unguarded (see "Deviations and decisions" below) since it renders nothing.

## Acceptance criteria

- Valid credentials create a session (hashed token persisted, ~14-day expiry) and set a `HttpOnly`, `SameSite=Lax` cookie; the frontend then navigates to `/workspaces`.
- An incorrect password and a nonexistent email return the identical `401 INVALID_CREDENTIALS` response — no user-enumeration signal, including no `Set-Cookie` on failure.
- Invalid input returns `422 VALIDATION_ERROR`; the plaintext password never appears in a response or log; the raw session token never appears in a response body (only the cookie carries it).

## Deviations and decisions made during implementation

- **"Remember me" dropped from the Figma source.** It implies variable session length, but the accepted decision fixes a flat 14-day TTL with no such semantics defined. Rendering it would promise unimplemented behavior — the same reasoning that dropped "Full name" from the registration screen.
- **"Forgot password?" kept as a plain, non-functional button**, matching Figma's own reference exactly (it has no handler there either). Password reset remains deferred.
- **`/workspaces` is unguarded.** It fetches and renders nothing, so gating it would mean building route-guard infrastructure with no other current purpose. This is the one choice with real architectural weight and needs revisiting once a screen there actually needs auth.
- **Login failures are always a form-level banner, never an inline field error** — unlike registration's duplicate-email case, placement itself could leak whether an email is registered.

## Required tests

- Backend integration: successful login (response shape, cookie attributes, persisted session row with correct hash and expiry), email normalization matching registration, wrong-password and nonexistent-email returning identical responses, validation errors, extra fields rejected, password/hash/raw token never in the response, no plaintext password in logs, unexpected errors don't leak details. Schema tests for the `sessions` table, its constraint names, and cascade-on-user-delete. Unit tests for the new token-hashing helpers.
- Frontend: no "Remember me" checkbox, password-visibility toggle, required-field validation, request body is exactly `email`/`password`, successful login navigates to `/workspaces`, invalid-credentials banner (focused, values preserved, never inline), generic-error banner, network-failure banner, "Create account" link target.

## Required verification

All backend and frontend commands listed under "Commands" in `CLAUDE.md`.

## Assumptions and unresolved questions

None outstanding for this slice's scope. The unguarded-`/workspaces` choice above is a known, explicitly flagged gap for whichever task first needs a real protected route.
