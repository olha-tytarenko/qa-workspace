---
name: qa-workspace-testing
description: >
  Design, implement, review, and maintain automated tests for QA Workspace.
  Use when adding or changing product behavior, fixing regressions, testing
  frontend components, backend APIs, domain rules, PostgreSQL persistence,
  background jobs, SSE events, authorization, AI-generation pipelines, or
  critical end-to-end workflows. Use this skill to select the smallest
  reliable test layer, preserve product invariants, and keep tests
  deterministic, behavior-focused, and maintainable.
---

# QA Workspace Testing

Build confidence in product behavior through focused, deterministic tests.

Tests must verify externally meaningful behavior and domain guarantees, not
mirror the internal structure of the implementation.

Follow the testing principles used in large engineering organizations:

- prefer many fast and isolated tests over a large slow suite;
- verify contracts at system boundaries;
- keep tests hermetic and deterministic;
- reserve end-to-end tests for critical user journeys;
- treat flaky tests as defects;
- use production-like dependencies where their behavior matters;
- optimize for useful confidence, not maximum coverage percentage.

## Infrastructure status

Currently in the repository: FastAPI, async SQLAlchemy with asyncpg, Alembic,
PostgreSQL, and backend pytest tests. The frontend has no test runner.

Target architecture, **not present unless the repository shows otherwise**:
Redis, a task queue, background workers, SSE, and an AI provider. The sections
on background jobs, SSE, AI generation, and the Redis/worker, SSE, and
live-model CI workflows describe how to test these components when they exist
or when an approved, scoped task introduces them.

- Before writing tests for any of them, inspect `compose.yaml`,
  `pyproject.toml`, and the application code to confirm the component exists.
- Mentioning a technology here does not authorize installing or configuring
  it. Redis, a worker or queue, SSE, or an AI provider may be introduced only by
  an explicitly approved, scoped implementation task.
- If a task needs one of them and it is absent, test the parts that exist and
  report the missing infrastructure. Do not create fake infrastructure to have
  something to test.

## Required context

Before designing tests:

1. Read the applicable product context.
2. Identify the user-visible behavior being changed.
3. Identify the domain invariants affected by the change.
4. Determine which boundaries are involved:
    - browser UI;
    - frontend state;
    - HTTP API;
    - authorization;
    - database;
    - background job;
    - SSE stream;
    - external AI provider.
5. Select the narrowest test layer that can reliably verify the behavior.

Use the following related skills when relevant:

- `qa-workspace-product-context` for terminology, workflow, and product rules;
- `qa-workspace-implement-feature` for end-to-end feature delivery;
- `qa-workspace-evolve-domain-model` for entity and persistence changes;
- `qa-workspace-frontend-patterns` for frontend behavior;
- `qa-workspace-backend-api-patterns` for API and worker behavior;
- `qa-workspace-ai-generation` for prompts, structured outputs, and AI
  evaluation.

## Testing priorities

Prioritize tests according to product risk.

The highest-risk QA Workspace behaviors include:

1. cross-workspace data isolation;
2. authorization and workspace membership;
3. preservation of approved or manually edited content;
4. distinction between generated and approved content;
5. requirement-level traceability;
6. correctness of coverage links;
7. idempotency of background jobs;
8. regeneration and stale-result handling;
9. validation of AI-generated structured output;
10. recovery from external provider and infrastructure failures.

A test suite that protects these behaviors is more valuable than a suite with
high line coverage but weak domain assertions.

## Test layers

Use four primary test layers.

### Unit tests

Use unit tests for isolated domain behavior and deterministic transformations.

Good candidates include:

- domain policies;
- permission decisions;
- state transitions;
- validation rules;
- coverage calculations;
- structured AI-output validation;
- mapping between domain objects and transport schemas;
- pure parsing and formatting functions.

Unit tests should not require:

- a browser;
- network access;
- PostgreSQL;
- Redis;
- a task queue;
- an external AI provider.

Do not mock the object being tested.

### Component tests

Use frontend component tests to verify behavior visible to the user within a
screen or coherent UI region.

Good candidates include:

- forms and validation;
- loading, empty, error, and success states;
- review and approval controls;
- permission-dependent actions;
- generated-content indicators;
- traceability and coverage presentation;
- keyboard and focus behavior;
- confirmation or conflict states.

Component tests may use a real router, query client, and form state when those
are part of the component's normal environment.

Mock the network boundary with MSW instead of mocking application hooks or
TanStack Query internals.

### Integration tests

Use integration tests when confidence depends on collaboration between real
components.

Good candidates include:

- FastAPI route, dependency, service, and repository behavior;
- SQLAlchemy persistence against PostgreSQL;
- transaction boundaries;
- authorization with workspace membership;
- database constraints;
- migrations;
- job persistence and dispatch;
- worker state transitions;
- SSE event production;
- API error contracts.

Do not replace PostgreSQL with SQLite when PostgreSQL-specific behavior,
transactions, constraints, JSON fields, concurrency, or query semantics are
relevant.

### End-to-end tests

Use Playwright for a small number of critical user journeys through the
browser and deployed application stack.

End-to-end tests should prove that essential workflows are connected
correctly. They should not duplicate every validation rule or edge case
already covered at lower layers.

## Choosing the test layer

Use the lowest layer that provides meaningful confidence.

Examples:

| Behavior | Preferred layer |
|---|---|
| Requirement status transition | Unit |
| Zod form validation and displayed message | Component |
| Workspace authorization at an API endpoint | Integration |
| PostgreSQL uniqueness or foreign-key rule | Integration |
| Worker retry and idempotency behavior | Integration |
| User reviews and approves generated criteria | End-to-end |
| Prompt quality across realistic examples | AI evaluation |
| Provider response schema validation | Unit or integration |

Add a higher-layer test only when it protects an important integration that
lower-layer tests cannot prove.

## General test design

Each test should communicate:

- the initial state;
- the action;
- the observable result;
- the domain rule being protected.

Prefer names that describe behavior:

```text
preserves_approved_acceptance_criteria_when_requirement_is_regenerated
```

Avoid names based only on implementation units:

```text
test_update_method
```

Use Arrange–Act–Assert or Given–When–Then consistently, but do not add comments
that merely repeat the code.

A test should normally fail for one meaningful reason.

## Behavior over implementation

Test through stable public interfaces.

Prefer assertions about:

- rendered information;
- available user actions;
- HTTP responses;
- persisted records;
- emitted domain or SSE events;
- job states;
- observable side effects.

Avoid assertions about:

- private methods;
- internal component state;
- hook call counts;
- CSS implementation classes;
- exact internal function sequences;
- ORM implementation details unrelated to behavior.

Refactoring internal code should not require rewriting tests when behavior
remains unchanged.

## Determinism and isolation

Tests must be repeatable locally and in CI.

Control sources of nondeterminism:

- time;
- random values;
- generated identifiers;
- environment configuration;
- network access;
- asynchronous scheduling;
- test execution order;
- shared database state.

Use fixed clocks or injectable clock abstractions when behavior depends on
time.

Use deterministic factories or explicitly supplied identifiers when identity
is relevant to assertions.

A test must not depend on another test having run first.

Do not call real external AI services in the normal automated test suite.

## Test data

Use small factories or builders that produce valid domain objects with useful
defaults.

Allow each test to override only the fields relevant to its scenario.

Prefer:

```python
requirement = requirement_factory(
    workspace_id=workspace.id,
    status="approved",
)
```

over large shared fixtures containing unrelated projects, users, requirements,
and generated artifacts.

Test data should make workspace and ownership boundaries explicit.

Avoid global fixtures that hide important setup or allow state to leak between
tests.

## Frontend tests

Use:

- Vitest as the frontend test runner;
- React Testing Library for component behavior;
- `userEvent` for user interaction;
- MSW for HTTP boundary mocking;
- Playwright for browser-level workflows.

### Query elements as users perceive them

Prefer queries in this order:

1. accessible role and name;
2. label text;
3. visible text;
4. stable semantic test identifier as a last resort.

Prefer:

```typescript
screen.getByRole("button", { name: /approve/i })
```

Avoid selecting elements by:

- CSS class;
- implementation-specific DOM structure;
- generated identifier;
- component instance;
- internal React state.

Use `data-testid` only when the element has no reliable accessible or semantic
selector.

### Interact like a user

Use `userEvent` for typing, clicking, selecting, and keyboard interaction.

Assert the resulting user-visible behavior instead of checking event handler
calls.

Use asynchronous queries and assertions for asynchronously rendered content.

Do not add arbitrary delays or manually poll the DOM.

### Mock at the network boundary

Use MSW handlers for API responses.

Do not normally mock:

- TanStack Query hooks;
- the API client method inside a component test;
- React Router navigation internals;
- React Hook Form internals.

Network-boundary mocking keeps component tests close to real application
behavior while remaining deterministic.

### Required frontend states

For meaningful data-driven screens, consider:

- initial loading;
- successful response;
- empty response;
- recoverable error;
- forbidden action;
- validation failure;
- stale or conflicting data;
- background operation in progress;
- completed background operation.

Add only states relevant to the changed behavior.

### QA Workspace frontend invariants

When relevant, verify that:

- generated content is visibly distinguishable from approved content;
- AI suggestions are not approved automatically;
- the user can inspect generated content before accepting it;
- edit, approve, and reject actions follow permissions;
- regeneration does not silently replace approved content;
- requirements and covered test cases remain traceable;
- ambiguous or missing information is presented rather than invented.

### Snapshots

Do not use large component or page snapshots as the primary assertion.

Small snapshots may be used for stable serialized structures when a snapshot
makes changes easier to review than explicit assertions.

A snapshot must not replace assertions about important behavior.

## Backend tests

Use pytest for backend tests.

Separate pure domain tests from tests requiring application infrastructure.

### API tests

Test the API through its public HTTP interface.

Verify:

- response status;
- structured response body;
- stable application error code;
- authorization behavior;
- persisted state;
- relevant side effects.

Do not assert only the HTTP status when the error contract matters.

For negative cases, distinguish between:

- unauthenticated;
- unauthorized;
- resource not found;
- invalid input;
- invalid state transition;
- conflict;
- unavailable dependency.

Do not reveal the existence of resources from another workspace when the
authorization model requires isolation.

### Authorization and tenancy

For every workspace-owned resource type, include tests proving that:

- an allowed member can perform the action;
- a member without the required permission cannot perform it;
- a user from another workspace cannot access it;
- identifiers from different workspaces cannot be combined;
- background jobs preserve the workspace boundary.

Test authorization on the server even when the frontend hides unavailable
actions.

### Database integration

Run persistence-sensitive tests against PostgreSQL.

Verify important database guarantees directly, including:

- foreign-key integrity;
- uniqueness;
- ownership consistency;
- transaction rollback;
- delete behavior;
- ordering where contractually relevant;
- concurrent or duplicate writes where relevant.

Use a clean transaction, schema, or isolated database namespace for each test
according to the repository's test infrastructure.

Do not weaken production constraints to make tests easier.

### Migrations

For significant schema changes, verify that:

- migrations apply successfully from the supported previous state;
- existing data remains valid;
- required backfills are correct;
- new constraints can be applied safely;
- downgrade behavior is tested only when downgrades are an actual supported
  operational requirement.

Do not treat successful model creation on an empty database as migration
testing.

## Background job tests

Applies when a job or worker system exists or is introduced by an approved,
scoped task. Inspect the repository first; none is configured by default.

Background jobs may be delivered more than once, delayed, retried, or executed
after the initiating state has changed.

Test relevant cases:

- successful execution;
- transient failure and retry;
- permanent failure;
- duplicate delivery;
- idempotent re-execution;
- cancellation;
- execution after the source requirement changed;
- execution after access or ownership changed;
- invalid provider output;
- result persistence failure;
- notification failure after successful persistence.

Persist the job or generation run before dispatching work.

The worker must load authoritative state by identifier instead of trusting a
large serialized snapshot from the queue.

For duplicate delivery, verify the final persisted state, not only the number
of worker invocations.

## SSE tests

Applies when an SSE endpoint exists or is introduced by an approved, scoped
task. Inspect the repository first; none is configured by default.

Test SSE as a notification mechanism, not as the only source of truth.

Verify:

- authentication and workspace authorization;
- documented event type;
- resource or operation identifier;
- terminal success and failure states;
- reconnect or refetch behavior;
- cleanup after client disconnect;
- behavior when events are missed;
- absence of long-lived database transactions.

The client should be able to recover current state from the normal API after a
disconnect or missed event.

Do not require exact timing between worker completion and browser rendering.

## AI-generation tests

Applies when AI-generation code exists or is introduced by an approved, scoped
task. No AI provider is configured by default, and the provider is not selected.
Test against a provider-independent interface and a fake, never against a
provider assumed from this document.

Normal CI must not depend on a live language model.

Use a deterministic fake or mocked provider to test:

- context selection;
- prompt and schema version propagation;
- structured-output parsing;
- validation;
- domain reference resolution;
- invalid or incomplete output;
- provider timeout;
- rate limiting;
- retry classification;
- persistence;
- provenance;
- approval boundaries;
- regeneration behavior.

### Product invariants

Tests must prove that:

- generated content begins as a proposal;
- generation never grants human approval;
- invalid output is not persisted as valid domain content;
- generated references cannot escape the current workspace;
- approved or manually edited content is not overwritten by regeneration;
- a new generation can be distinguished from an earlier generation;
- stale results cannot silently replace newer accepted work;
- failures remain visible and auditable.

### Semantic AI evaluations

Use separate AI evaluations for questions such as:

- whether findings are relevant;
- whether ambiguity detection is useful;
- whether acceptance criteria are testable;
- whether generated test cases cover the requirement;
- whether unsupported assumptions are introduced.

Semantic evaluations belong to the AI-generation evaluation workflow and
should run separately from deterministic pull-request tests.

Do not make the normal CI pipeline depend on live-model wording or exact
natural-language output.

## End-to-end testing with Playwright

Keep the end-to-end suite small and high-value.

Recommended QA Workspace journeys include:

1. user enters an authorized workspace;
2. user creates a feature and requirement;
3. requirement analysis produces reviewable suggestions;
4. user edits, approves, or rejects generated content;
5. user generates acceptance criteria and test cases;
6. test cases remain linked to their requirements;
7. coverage status reflects confirmed traceability;
8. regeneration preserves previously approved work.

Use a deterministic AI provider or controlled test mode for these flows once
the AI-generation feature exists. Journeys that depend on absent functionality
cannot be written yet.

### Playwright practices

- use role-, label-, and text-based locators;
- use web-first assertions;
- let Playwright wait for observable conditions;
- avoid fixed sleeps;
- isolate data for each test;
- avoid shared mutable user accounts or workspaces;
- create preconditions through stable APIs when the UI action itself is not
  under test;
- keep one clear user journey per test;
- collect trace, screenshot, and relevant logs on failure;
- run tests against production-like builds where practical.

Do not test behavior owned by an external service through that service's UI.

## Regression testing

When fixing a defect:

1. identify the violated behavior or invariant;
2. reproduce it with the narrowest reliable automated test;
3. confirm that the test fails for the expected reason;
4. implement the fix;
5. confirm that the new test and relevant existing tests pass;
6. add a higher-level test only when the defect involved an unprotected
   integration boundary.

Do not create a regression test that merely reproduces the previous
implementation.

## Flaky tests

Treat flaky tests as product and engineering defects.

When a test is flaky:

1. reproduce and collect evidence;
2. identify the uncontrolled dependency or race;
3. remove the nondeterminism;
4. improve synchronization through observable state;
5. verify the fix under repeated execution.

Do not solve flakiness by:

- adding arbitrary sleeps;
- permanently increasing timeouts;
- weakening assertions;
- ignoring the test;
- relying only on automatic retries.

Retries may collect diagnostic evidence, but they do not make a flaky test
healthy.

## Coverage

Use coverage reports to identify untested risk, not as the definition of
quality.

Do not pursue 100% line coverage by testing trivial accessors or
implementation details.

Review coverage for:

- domain invariants;
- error paths;
- authorization branches;
- state transitions;
- persistence constraints;
- async failure modes;
- critical user journeys.

A high coverage number does not compensate for missing assertions about
important behavior.

## Continuous integration

Organize tests by cost and purpose. This describes the target pipeline. No CI
configuration exists in the repository yet, and each workflow below applies only
to components that exist.

### Pull-request checks

Run:

- formatting and static analysis;
- type checking;
- fast unit tests;
- frontend component tests;
- backend integration tests that fit the agreed PR budget;
- deterministic AI-pipeline tests.

### Integration workflow

Run:

- full PostgreSQL integration suite;
- Redis and background-worker integration, once they exist;
- migration verification;
- SSE integration, once it exists;
- broader cross-service tests.

### End-to-end workflow

Run:

- critical Playwright journeys;
- supported browser coverage;
- production-like frontend build;
- failure artifact collection.

### AI evaluation workflow

Once an AI provider has been introduced by an approved task, run live-model
evaluations separately:

- on prompt or model changes;
- on a schedule;
- before intentional provider or model migration;
- when evaluation datasets change.

A live-model evaluation failure should report the affected quality dimension
and examples, not only a single aggregate score.

## Test review checklist

Before completing a change, verify:

- Is the tested behavior important to a user or domain rule?
- Is this the narrowest reliable test layer?
- Does the test use stable public interfaces?
- Is the test deterministic?
- Is test data isolated?
- Are workspace boundaries explicit?
- Are important negative paths covered?
- Does the test protect AI human-approval boundaries?
- Does it preserve approved content during regeneration?
- Are external services controlled?
- Are asynchronous assertions based on observable state?
- Would the test survive a safe internal refactor?
- Does the test failure clearly explain what behavior broke?

## Expected output

When asked to design or review tests, provide only the sections that add value.

### Behavior under test

State the user-visible behavior or domain invariant.

### Risk

Explain what failure the test is intended to detect.

### Selected test layer

State the layer and why it provides sufficient confidence.

### Test scenarios

List meaningful positive, negative, permission, state, and failure scenarios.

### Test data and boundaries

Describe required workspace membership, records, external dependencies, and
controlled inputs.

### Verification

State the exact commands or checks that were actually executed.

Do not claim that tests passed unless they were run successfully.

## Prohibited behavior

Do not:

- test implementation details instead of behavior;
- call a live AI provider from the normal CI suite;
- use SQLite as a transparent substitute for PostgreSQL;
- mock every internal layer in an integration test;
- mock TanStack Query hooks in normal component tests;
- rely on execution order;
- share mutable state between tests;
- use arbitrary sleeps for asynchronous behavior;
- approve generated content implicitly in fixtures or helpers;
- hide cross-workspace authorization failures;
- overwrite approved artifacts during regeneration tests;
- use retries as the primary solution to flakiness;
- pursue coverage percentage at the expense of meaningful assertions;
- create broad end-to-end tests for behavior that can be verified reliably at
  a lower layer;
- report tests as passing without executing them.