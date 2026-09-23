# Task: User registration

## Goal

Let a new user create an account with an email and password, as the first step toward the product's open-registration MVP (`docs/decisions.md` §1).

## User-visible outcome

A user can open `/auth/sign-up`, submit an email and password, and see a confirmation that their account was created. Validation and error states (missing fields, mismatched passwords, too-short password, duplicate email, server error) are shown inline without losing entered values.

## Scope

- Backend: `POST /api/auth/register`, `User` model and migration, Argon2id password hashing, the fixed error envelope, CORS middleware.
- Frontend: the `/auth/sign-up` screen (form, validation, success and error states), translated from the Figma Make source.

## Explicit non-goals

Sign-in implementation and page, sessions/cookies, `/api/auth/me`, logout, protected routes, workspace creation, workspace/membership models, roles/authorization, email verification, password reset, rate limiting/CAPTCHA, Redis/workers/SSE/AI integration, Playwright, CI/CD changes.

## Relevant accepted decisions

`docs/decisions.md` §1 (open registration, email+password auth), §2 (Argon2id, CORS), §4 (API conventions), §5 (SQLAlchemy/Alembic conventions). This task's approval updated §2's CORS timing and added the `data`-envelope success convention to §4 — see the diff to `docs/decisions.md` in the same change.

## API or data-model impact

- New table `users` (`id` uuid pk, `email` unique, `password_hash`, `created_at`), one new Alembic migration.
- New endpoint `POST /api/auth/register` → `201` with `{"data": {"id", "email", "created_at"}}`, or the fixed error envelope (`422` validation, `409` duplicate email, `500` unexpected).

## Authorization rules

None — registration is open per `docs/decisions.md` §1.

## Acceptance criteria

- Valid submission creates a user with a hashed password and returns the public user shape.
- Duplicate email (case/whitespace-insensitive) returns `409 EMAIL_ALREADY_REGISTERED`.
- Invalid input returns `422 VALIDATION_ERROR`; the plaintext password never appears in a response or log.
- Frontend: matches the current Figma Make `/auth/sign-up` source, with the deviations below. CORS allows the configured frontend origin only, with credentials, no wildcard.

## Deviations from the Figma source (approved)

- **Full name field removed.** Figma's sign-up form has a "Full name" input. The approved data model and API contract are email+password only; a field that goes nowhere would be misleading, so it is not rendered, not sent, and not validated. The success-state copy's own `name || 'there'` fallback (from the Figma source) is used as-is, since there is no name to substitute.
- **Password requirements copy replaced.** Figma shows three rules ("At least 8 characters", "One uppercase letter", "One number"); the actual policy is "at least 12 characters, no character-class rules." The checklist shows a single "At least 12 characters" item in the same visual treatment.
- **Success-state action removed.** The current Figma source's success state has one action, "Go to my workspace" → `navigate('/workspaces')`. Building `/workspaces` is out of scope for this slice, and per explicit human decision the button is not implemented at all — the success state shows only the confirmation message and icon, no action.
- **Duplicate-email and generic-error states are not designed in Figma.** Duplicate email reuses the existing `Input` error pattern on the email field; generic/network errors reuse the red banner pattern from `SignIn.tsx`, the closest existing analog in the same source.

## Required tests

- Backend integration: successful registration, email normalization, password hashing, validation errors (missing/invalid email, short/long password, extra fields), duplicate email (exact/case/whitespace variants), password/hash never in the response, no plaintext password in logs, unexpected errors don't leak details, CORS allowed/disallowed origin. Schema tests for the `users` table and its constraint names. Unit tests for `hash_password`/`verify_password`, including a non-BMP password.
- Frontend: form renders without a Full name field, required-field validation, password-mismatch validation, password-length validation (including a non-BMP-character case proving code-point counting), request body contains only `email`/`password`, success state (no action button/link), duplicate-email inline error with focus, generic-error banner with focus and no leaked details, network-failure banner, sign-in link target.

## Required verification

All backend and frontend commands listed under "Commands" in `CLAUDE.md`.

## Assumptions and unresolved questions

None outstanding — the one open question (the success-state button's destination) was resolved by explicit human decision: remove the button.
