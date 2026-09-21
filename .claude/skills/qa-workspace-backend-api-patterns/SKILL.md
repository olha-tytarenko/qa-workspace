---
name: qa-workspace-backend-api-patterns
description: >
  Apply QA Workspace backend and API architecture patterns when creating or
  changing FastAPI endpoints, Pydantic schemas, application services,
  repositories, SQLAlchemy persistence, PostgreSQL transactions, authorization,
  background jobs, SSE streams, error contracts, pagination, idempotency, or
  external integrations. Use for backend implementation and review. Do not use
  for frontend-only work, prompt design, or database changes that do not affect
  backend behavior.
---

# QA Workspace Backend and API Patterns

Build QA Workspace backend functionality using Python, FastAPI, Pydantic,
async SQLAlchemy 2 (asyncpg), Alembic, and PostgreSQL.

Expose resource-oriented REST APIs for synchronous operations. The target
architecture runs long-running AI operations as persisted asynchronous jobs
with SSE notifications; see "Infrastructure status" below before relying on it.

Keep transport, application, domain, and persistence responsibilities
separate.

## Infrastructure status

Currently configured: FastAPI, async SQLAlchemy with asyncpg, Alembic, and
PostgreSQL.

Target architecture, **not configured unless the repository shows otherwise**:
Redis, a task queue (Celery, Dramatiq, or another), background workers, and
SSE. The sections on jobs, generation runs, workers, cancellation, and SSE
describe how to build these when they exist. They do not describe the current
repository.

- Before using or assuming any of them, inspect `compose.yaml`,
  `pyproject.toml`, and the application code. Do not refer to a "configured"
  queue, worker system, Redis client, or SSE helper that you did not find.
- Introduce Redis, a queue, workers, or SSE only inside an explicit, scoped
  implementation task that approves that infrastructure. Do not add it as a
  side effect of another feature, and do not add a second queue framework once
  one exists.
- When the infrastructure does not exist, do not fake it. Implement only the
  synchronous part of the task, or stop and report that the asynchronous
  infrastructure is a prerequisite.
- The architectural rules below (persisted job state, commit before enqueue,
  duplicate delivery, SSE as a notification channel) still apply in full when
  that infrastructure is introduced.

## Establish context

Before changing backend behavior:

1. Apply `qa-workspace-product-context` when product behavior or terminology is
   involved.
2. Apply `qa-workspace-evolve-domain-model` when changing entities,
   relationships, invariants, ownership, or lifecycle transitions.
3. Inspect existing routers, request and response schemas, services,
   repositories, ORM models, migrations, authorization checks, and tests.
4. Identify all API and background-job consumers.
5. Determine the transaction, authorization, and workspace boundaries.
6. Identify whether the operation is synchronous, asynchronous, or streaming.
7. Search for an existing comparable endpoint before creating a new pattern.

Follow established repository conventions unless they conflict with explicit
requirements, domain invariants, security, or correctness.

## Preserve architectural boundaries

Prefer this dependency direction:

```text
HTTP and SSE transport
        ↓
application services
        ↓
domain model
        ↓
repository interfaces
        ↓
SQLAlchemy and external integrations
```

Responsibilities:

- routers handle HTTP transport;
- Pydantic schemas validate and serialize boundary data;
- application services coordinate use cases;
- domain code enforces business rules and state transitions;
- repositories load and persist aggregates or domain entities;
- infrastructure code implements database, queue, AI-provider, and external
  service access.

Do not let domain code depend on FastAPI, SQLAlchemy, Redis, Celery, Dramatiq,
or HTTP concepts.

Do not put business workflows directly in route handlers.

Do not use repositories as generic query containers for unrelated entities.

Avoid adding layers that only forward identical arguments without enforcing a
boundary or policy.

## Keep route handlers thin

A route handler may:

1. parse path, query, header, and body values;
2. resolve the authenticated user;
3. invoke one application use case;
4. map the result to a response schema;
5. translate known application failures into the standard API error contract.

A route handler must not:

- construct complex SQL queries;
- implement domain state transitions;
- authorize access through client-provided ownership values alone;
- call an LLM directly;
- enqueue background work before the transaction commits;
- expose ORM objects as responses;
- catch every exception and return a generic success response.

## Design APIs around resources

Model the API around domain resources and their ownership relationships.

Primary resources may include:

- workspaces;
- workspace memberships;
- projects;
- features;
- requirements;
- requirement analyses;
- findings;
- clarification questions;
- acceptance criteria;
- test cases;
- coverage links;
- generation runs.

Accepted conventions (see `docs/decisions.md`): every endpoint is served under
the `/api` prefix (the examples below omit it for brevity), persisted entity
primary keys are UUIDv4, CRUD uses ordinary RESTful routes, and `:action` routes
are reserved for genuine domain commands.

Prefer standard HTTP operations where their semantics fit:

```text
POST   /workspaces
GET    /workspaces/{workspace_id}
PATCH  /workspaces/{workspace_id}
DELETE /workspaces/{workspace_id}

POST   /workspaces/{workspace_id}/projects
GET    /workspaces/{workspace_id}/projects
GET    /projects/{project_id}
PATCH  /projects/{project_id}
DELETE /projects/{project_id}
```

Use nested collection routes to express ownership during creation and listing.

A resource may use a shorter canonical item route when its identifier is
globally unique, but authorization must still resolve and verify the complete
ownership path.

Do not mirror database tables mechanically in the public API.

Do not expose internal join tables when the relationship has no user-visible
meaning.

## Use explicit domain actions

Use standard create, get, list, update, and delete operations for ordinary
resource lifecycle changes.

Use an explicit action endpoint when an operation represents a domain command
rather than arbitrary field mutation.

Examples include:

```text
POST /requirements/{requirement_id}:submit-for-review
POST /requirements/{requirement_id}:approve
POST /requirements/{requirement_id}:reject
POST /features/{feature_id}:analyze
POST /features/{feature_id}:generate-test-cases
POST /generation-runs/{generation_run_id}:cancel
```

Use the repository's established URI convention for custom actions
consistently. Do not mix several action styles without reason.

Do not allow clients to perform protected transitions by setting fields such
as `status: "approved"` through a generic update endpoint.

The server must validate the current state, actor permission, and transition
preconditions.

## Define request and response schemas explicitly

Use separate Pydantic models for:

- create requests;
- update requests;
- action requests;
- public responses;
- list responses;
- error responses.

Do not use SQLAlchemy models as API schemas.

Do not reuse one schema for create, update, persistence, and response when the
fields have different mutability or security rules.

Classify fields as:

- client-required;
- client-optional;
- server-generated;
- immutable;
- output-only;
- nullable;
- omitted when unavailable.

Do not accept server-controlled fields such as:

- identifiers;
- ownership identifiers derived from the route;
- approval actor;
- approval timestamps;
- provenance;
- generation status;
- audit metadata.

Reject unknown fields when silently accepting them could hide a client error
or security issue.

## Distinguish omission from null

For partial updates, distinguish:

- a field omitted from the request;
- a field explicitly set to `null`;
- a field set to a concrete value.

Apply only explicitly supplied fields.

Do not convert omission into `null`.

Do not allow `null` for a field unless clearing that field has defined domain
meaning.

Prefer explicit action endpoints for lifecycle transitions instead of encoding
them as partial updates.

## Return stable resource representations

Return the canonical public representation of a resource after a successful
create or update when practical.

Use stable field names and types across get, create, and update responses.

Keep internal implementation details out of responses, including:

- database sequence values that are not public identifiers;
- internal queue names;
- provider-specific AI response structures;
- raw exception messages;
- internal storage paths;
- authorization implementation details.

Add fields compatibly when possible.

Do not remove or reinterpret an existing response field without identifying
and updating its consumers.

## Enforce authentication and authorization separately

Authentication establishes who the caller is.

Authorization determines whether that caller may perform the requested action
on the requested resource.

Do not treat successful authentication as authorization.

For every workspace-owned operation:

1. Resolve the authenticated user from trusted authentication data.
2. Resolve the target resource through its stored ownership path.
3. Resolve the user's workspace membership.
4. verify the membership status;
5. verify the role or specific permission;
6. enforce the requested domain operation;
7. reject cross-workspace references.

Do not authorize a request solely because:

- the client supplied a `workspace_id`;
- the user knows a resource identifier;
- the resource was found by a global primary key;
- the frontend hid the action;
- the user has membership in a different workspace.

Apply authorization to read operations as well as mutations.

## Prevent object-level authorization failures

Load workspace-owned resources through an authorization-aware query or verify
ownership immediately after loading them.

For relationships, validate every referenced object.

For example, before creating a coverage link, verify that:

- the user can access the workspace;
- the requirement belongs to an accessible feature;
- the test case belongs to the same feature;
- neither resource belongs to another workspace;
- the relationship satisfies domain invariants.

Do not accept arbitrary foreign keys from the request and persist them before
checking ownership.

Policy (accepted, see `docs/decisions.md`): a request for a workspace resource
by a non-member returns `404`, never `403`, so existence is not leaked. `403`
is only for an authenticated member who lacks the role required for the action.

## Use predictable HTTP semantics

Use status codes consistently:

- `200 OK` for successful reads and updates with a response body;
- `201 Created` for synchronously created resources;
- `202 Accepted` when work has been accepted but continues asynchronously;
- `204 No Content` for successful operations with no response body;
- `400 Bad Request` for malformed requests not covered by schema validation;
- `401 Unauthorized` when authentication is missing or invalid;
- `403 Forbidden` when the authenticated user lacks permission;
- `404 Not Found` when an accessible resource does not exist;
- `409 Conflict` for state conflicts or duplicate operations;
- `412 Precondition Failed` for failed version preconditions when used;
- `422 Unprocessable Entity` for structured validation failures;
- `429 Too Many Requests` for enforced rate limits;
- `500 Internal Server Error` for unexpected server failures;
- `503 Service Unavailable` for temporary dependency unavailability.

Do not return `200` with an error encoded only inside the response body.

Do not expose internal stack traces or exception strings.

## Standardize error responses

Use one machine-readable error envelope across the API. Its shape below is the
fixed API error format (see `docs/decisions.md`); the values are illustrative.
`request_id` is a correlation identifier, not an entity primary key.

For example:

```json
{
  "error": {
    "code": "INVALID_STATE_TRANSITION",
    "message": "The requirement cannot be approved while it is in draft state.",
    "details": {
      "resource_id": "req_123",
      "current_status": "draft",
      "required_status": "in_review"
    },
    "request_id": "request_123"
  }
}
```

The error contract should provide:

- a stable machine-readable `code`;
- a concise and actionable `message`;
- structured `details` when useful;
- a request or correlation identifier.

Clients must branch on `code`, not parse `message`.

Keep error codes stable after clients depend on them.

Do not include secrets, credentials, prompts, stack traces, SQL, or sensitive
cross-workspace information in errors.

Map expected domain and application failures explicitly. Let unexpected
failures reach centralized exception handling and monitoring.

## Validate at the correct boundary

Use Pydantic for transport-level validation, including:

- required fields;
- basic format;
- length and range constraints;
- enum membership;
- structural validation.

Use application or domain logic for:

- permissions;
- ownership;
- uniqueness under concurrency;
- valid state transitions;
- cross-entity invariants;
- approval behavior;
- regeneration safety;
- coverage-link validity.

Use PostgreSQL constraints for invariants that must survive all write paths,
such as:

- foreign keys;
- required values;
- uniqueness;
- check constraints where appropriate.

Do not assume Pydantic validation protects writes performed outside the HTTP
request path.

## Control database transactions

Define transactions around application use cases, not individual repository
methods by default.

A use case should either persist all required state changes or none of them.

Do not commit from multiple nested repository calls without an explicit reason.

Do not hold a database transaction open while:

- calling an LLM;
- waiting for a background worker;
- streaming SSE events;
- calling a slow external service;
- performing long computation.

Persist the operation or job first, commit it, then dispatch external work.

If queue publication must be atomic with database state, use an established
transactional outbox or equivalent mechanism. Do not claim atomicity between
PostgreSQL and Redis without one.

Rollback failed transactions and avoid reusing a failed SQLAlchemy session.

## Use async SQLAlchemy

Database access is async: SQLAlchemy 2 `AsyncEngine`, `async_sessionmaker`,
and asyncpg.

- Use one `AsyncSession` per request or per worker operation. In routes, obtain
  it from the `get_session` dependency in `app/db/session.py`.
- The session does not commit implicitly. The application use case opens the
  transaction explicitly, for example `async with session.begin():`.
- Do not make blocking database calls, or other blocking I/O, inside
  `async def` code.
- Do not add a second PostgreSQL driver unless a tool constraint requires it
  and the reason is recorded.
- Load settings through `get_settings()` and create engines and sessions only
  at the application-lifecycle boundary, so importing modules never requires
  infrastructure configuration. Domain modules must not import them.

## Avoid inefficient data access

Inspect query behavior for list and nested-resource endpoints.

Avoid:

- N+1 relationship loading;
- loading complete object graphs for summaries;
- unbounded list queries;
- selecting large generated content when only metadata is required;
- repeated authorization queries that can be safely combined.

Fetch only the data required for the use case while keeping repository APIs
domain-oriented.

Add indexes for demonstrated access patterns, ownership checks, foreign keys,
sorting, and filtering.

Do not add speculative indexes without an identified query.

Verify query plans for endpoints where volume or latency is material.

## Paginate collections

Paginate collections that may grow with normal product usage.

Prefer cursor-based pagination for mutable or large collections.

A list response may include:

```json
{
  "items": [],
  "next_cursor": "opaque-value"
}
```

Keep cursors opaque to clients.

Use deterministic ordering with a stable tie-breaker.

Validate and reject malformed cursors.

Do not expose raw database offsets or implementation details as cursor
contracts.

Offset pagination may be used for small, bounded administrative collections
when its consistency limitations are acceptable.

Set and enforce a maximum page size.

## Support filtering and sorting deliberately

Expose only documented filter and sort fields.

Validate filter operators and values.

Do not translate arbitrary client strings directly into SQL column names or
expressions.

Use deterministic default ordering.

Keep query semantics stable after clients depend on them.

For complex filtering, use structured request models rather than inventing an
ambiguous mini-language without validation.

## Protect concurrent updates

Use optimistic concurrency for resources where stale writes could overwrite
reviewed or user-edited content.

A resource may expose an opaque version or revision value.

Require the expected version for sensitive updates, such as:

- editing reviewed requirements;
- updating approved artifacts;
- submitting review decisions;
- replacing generated suggestions;
- modifying coverage links during concurrent review.

Reject stale writes with a clear conflict or precondition error.

Do not silently apply a stale full-resource update over a newer version.

Do not add concurrency checks to append-only operations without an identified
lost-update risk.

## Make retryable writes idempotent

Design operations so safe retries do not create duplicate effects.

Support idempotency keys for operations where clients or infrastructure may
retry a non-idempotent request, including:

- starting a generation run;
- importing requirements (deferred; not part of the MVP);
- creating expensive background work;
- executing a retryable external side effect.

Scope the idempotency key to the authenticated caller and operation.

Persist:

- the key;
- a fingerprint of relevant request parameters;
- the resulting resource or response;
- an expiration policy.

When the same key is reused:

- return the original result when parameters match;
- reject the request when parameters differ;
- prevent concurrent duplicate execution.

Do not use idempotency keys as a substitute for database uniqueness or domain
invariants.

## Model AI work as persisted asynchronous jobs

This and the following job, worker, cancellation, and SSE sections apply when
the corresponding infrastructure exists or a task explicitly introduces it (see
"Infrastructure status"). Inspect the repository first.

Do not call the LLM directly from a request that may exceed normal API latency
or needs reliable retry, cancellation, or progress reporting.

Use this flow:

```text
API request
    ↓
validate and authorize
    ↓
create Generation Run in PostgreSQL
    ↓
commit transaction
    ↓
enqueue job
    ↓
worker calls AI provider
    ↓
validate structured output
    ↓
persist suggestions
    ↓
publish state notification
```

Return `202 Accepted` with the generation-run resource or its location.

The generation run is the authoritative record of job state.

Redis and the task queue are delivery infrastructure, not the source of truth.

Use the worker system found in the repository. If none exists, its
introduction needs an explicit scoped task. Do not introduce a second queue
framework for one feature.

## Define generation states explicitly

Use an explicit state machine for background work.

A baseline lifecycle may include:

```text
queued → processing → completed
                    → failed
                    → cancelled
```

Define allowed transitions and reject invalid transitions.

Persist useful timestamps such as:

- created;
- started;
- completed;
- failed;
- cancelled.

Record safe, structured failure information.

Do not persist raw provider errors if they may contain prompts, credentials, or
sensitive customer data.

A retry should either:

- continue the same generation run with recorded attempt metadata; or
- create a new run linked to the previous one.

Choose one model consistently.

## Process background jobs safely

A worker must:

1. load the persisted generation run;
2. verify that the run is still eligible for processing;
3. transition it atomically to `processing`;
4. load authoritative source data;
5. call the AI provider outside a long-lived database transaction;
6. validate the returned structure;
7. recheck relevant version or cancellation state;
8. persist suggestions and terminal status transactionally;
9. publish a notification after persistence succeeds.

Assume a job may be delivered more than once.

Make processing idempotent or detect duplicate delivery.

Do not let duplicate workers create duplicate accepted artifacts.

Do not allow an older generation run to replace output from a newer relevant
run without an explicit product rule.

## Treat AI output as untrusted

Validate AI output using explicit Pydantic schemas before persistence.

Validate:

- required fields;
- lengths and collection limits;
- enum values;
- referenced identifiers;
- ownership boundaries;
- domain invariants;
- allowed suggestion types.

Ignore or reject provider-supplied identifiers that could reference
authoritative resources.

The backend, not the model, assigns:

- resource identifiers;
- workspace and feature ownership;
- approval state;
- review actor;
- provenance;
- permissions.

Store valid output as AI-generated suggestions, never as automatically approved
artifacts.

Detailed prompt and evaluation rules belong to the AI-generation skill.

## Use SSE as a notification channel

Applies once SSE infrastructure exists or is introduced by an explicit scoped
task; do not assume an SSE implementation without inspecting the repository.

Use SSE for one-way updates about persisted asynchronous work.

An SSE stream may notify clients about:

- generation-run state changes;
- completion;
- failure;
- cancellation;
- availability of new persisted suggestions.

Do not treat the SSE connection as the only source of job state.

On connection or reconnection, clients must be able to fetch the authoritative
generation-run resource.

When supported, include:

- stable event types;
- event identifiers;
- heartbeat events or comments;
- reconnection behavior;
- authorization checks;
- safe event payloads.

Do not send credentials, raw prompts, provider responses, or unrelated
workspace data through the stream.

Stop streaming when the client disconnects.

Do not keep a database transaction or SQLAlchemy session open for the lifetime
of the SSE connection.

## Secure SSE subscriptions

Authenticate the stream using the application's established authentication
mechanism.

Authorize access to every subscribed resource.

Do not authorize a stream only once if it can later emit events for arbitrary
resource identifiers.

Use workspace-scoped channels or filter events through verified ownership.

Treat client-provided generation-run IDs and last-event IDs as untrusted input.

Avoid placing long-lived secrets in query parameters.

## Handle cancellation explicitly

Cancellation is a domain operation, not merely a disconnected HTTP request.

When cancellation is supported:

1. authorize the actor;
2. validate the current generation state;
3. persist a cancellation request or terminal cancellation state;
4. signal the worker when supported;
5. prevent later results from being persisted as active output;
6. return the authoritative generation-run state.

A provider call may not stop immediately. The worker must still check
cancellation before persisting results.

Do not claim that cancellation succeeded merely because the client closed the
SSE connection.

## Protect external integrations

Wrap external services behind explicit interfaces.

For each dependency, define:

- timeout;
- retry policy;
- retryable failures;
- rate-limit behavior;
- cancellation behavior;
- idempotency behavior;
- observability metadata;
- safe error translation.

Use bounded timeouts.

Retry only failures likely to be transient.

Use exponential backoff with jitter when retrying distributed dependencies.

Do not retry non-idempotent operations unless duplicate effects are prevented.

Do not expose provider-specific errors directly through the public API.

## Manage secrets and sensitive data

Load secrets from the configured environment or secret manager.

Never:

- hardcode credentials;
- commit local secret files;
- include tokens in logs;
- return secrets in API responses;
- place secrets in queue payloads unnecessarily;
- include authentication data in SSE events;
- expose raw prompts or customer content in exception traces.

Send the minimum required data to external AI providers.

Apply retention and logging rules consistently to requirements, generated
content, and prompts.

## Add abuse and resource controls

Bound all user-controlled resource consumption.

Set reasonable limits for:

- request-body size;
- imported requirement count (once importing exists; it is deferred);
- individual text length;
- generated item count;
- page size;
- concurrent generation runs;
- SSE connections;
- retry attempts;
- job runtime;
- external provider calls.

Apply rate limits according to authenticated user and workspace where
appropriate.

Do not rely on frontend limits for backend protection.

Return actionable limit errors without exposing internal capacity details.

## Log and observe safely

Use structured logs.

Include safe operational identifiers such as:

- request ID;
- user ID when policy allows;
- workspace ID;
- resource ID;
- generation-run ID;
- job attempt;
- endpoint or operation name;
- duration;
- outcome.

Do not log full access tokens, passwords, secrets, raw SQL parameters, or
complete prompts by default.

Propagate correlation identifiers from the API through background jobs and
external calls.

Record metrics for:

- request latency and error rate;
- authorization failures;
- queue delay;
- generation duration;
- provider failures;
- job retries;
- SSE connection failures;
- validation failures;
- rate limiting.

Do not use logs as the authoritative audit trail for product decisions.

## Preserve audit-relevant actions

Persist audit information for product actions where accountability matters,
including:

- approval and rejection;
- membership or role changes;
- destructive actions;
- generation-run creation and cancellation;
- changes to approved artifacts;
- confirmation of AI-proposed coverage links.

An audit record should identify:

- actor;
- action;
- target;
- workspace;
- timestamp;
- relevant prior and resulting state or version.

Do not store sensitive content in audit records unless required.

Do not allow ordinary application updates to rewrite historical audit records.

## Create safe migrations

Use Alembic for PostgreSQL schema changes.

Before writing a migration:

1. inspect current models and migration history;
2. identify existing data affected;
3. define backfill behavior;
4. assess lock and deployment risk;
5. determine compatibility with the currently deployed application;
6. define verification and rollback strategy.

Prefer expand-and-contract changes when old and new application versions may
temporarily coexist.

Do not:

- add a required column without a valid backfill or domain-derived default;
- drop data before consumers stop using it;
- invent fake domain values to satisfy a constraint;
- combine unrelated schema changes;
- modify an already-applied migration;
- assume ORM changes automatically update the database.

Require explicit human review before applying migrations outside a disposable
local or test database.

## Test backend behavior

Add or update tests for:

- successful requests;
- request validation;
- authentication;
- workspace authorization;
- cross-workspace isolation;
- missing resources;
- invalid state transitions;
- stable error codes;
- transaction rollback;
- idempotent retries;
- concurrent updates when relevant;
- background-job duplicate delivery;
- AI output validation;
- cancellation races;
- SSE authorization and reconnection behavior;
- migrations and constraints when changed.

Prefer integration tests for behavior spanning FastAPI, application services,
repositories, and PostgreSQL.

Mock external AI providers and other network dependencies in CI.

Do not mock the domain behavior being tested.

## Review backend changes

Before completing backend work, verify:

- route handlers remain thin;
- domain rules are not duplicated in transport code;
- authorization follows stored ownership;
- all referenced resources are workspace-safe;
- Pydantic and ORM models are not used interchangeably;
- transactions match complete use cases;
- external calls do not hold database transactions open;
- list endpoints are bounded;
- errors use stable machine-readable codes;
- retryable writes cannot duplicate effects;
- background jobs tolerate duplicate delivery;
- Redis is not treated as the source of truth;
- SSE exposes only authorized persisted state;
- AI output cannot assign ownership or approval;
- migrations preserve existing data;
- relevant tests and static checks pass.

Do not claim an endpoint is secure, idempotent, or concurrency-safe without
verifying the relevant behavior.