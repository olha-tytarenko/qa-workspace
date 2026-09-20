---
name: qa-workspace-code-review
description: >
  Review QA Workspace code changes for correctness, product consistency,
  security, workspace isolation, maintainability, and test coverage. Use when
  reviewing a pull request, diff, implementation, refactoring, migration, API
  change, frontend behavior, background job, SSE flow, or AI-generation
  pipeline. Report only evidence-backed problems introduced or exposed by the
  reviewed change. Do not use this skill to implement fixes unless the user
  explicitly requests them.
---

# QA Workspace Code Review

Review changes as a correctness and risk assessment.

The purpose of review is to identify concrete defects before they reach users,
not to demonstrate alternative coding preferences.

Prioritize:

1. product and domain correctness;
2. security and workspace isolation;
3. data integrity;
4. AI human-control guarantees;
5. failure and concurrency behavior;
6. compatibility with existing contracts;
7. missing tests for material risks;
8. maintainability when it creates a concrete future risk.

Do not block a change solely because it differs from a preferred style.

## Infrastructure status

Currently in the repository: FastAPI, async SQLAlchemy with asyncpg, Alembic,
and PostgreSQL. Redis, a task queue, background workers, SSE, and an AI
provider are target architecture and are **not present unless the repository
shows otherwise**.

- Inspect the repository before assuming any of them exists.
- The background-job, SSE, and AI-generation checks below apply when the
  reviewed change uses or introduces that infrastructure. Apply them in full
  then. Do not report a missing worker, queue, SSE stream, or provider as a
  defect in code that does not use one.
- A change that introduces any of them is in scope only if the task explicitly
  approved it. Report unapproved introduction of Redis, a queue, workers, SSE,
  or an AI provider as a scope finding, because mentioning a technology in a
  skill does not authorize it.

## Required context

Before reviewing:

1. Read the repository instructions.
2. Read `qa-workspace-product-context` and its relevant references.
3. Inspect the complete changed files, not only isolated diff fragments.
4. Inspect nearby callers, consumers, schemas, tests, and migrations when they
   affect the interpretation of the change.
5. Identify the user behavior and domain rules affected by the change.
6. Determine whether the change is complete across all affected layers.

Use related skills when relevant:

- `qa-workspace-evolve-domain-model` for domain and persistence changes;
- `qa-workspace-frontend-patterns` for React behavior;
- `qa-workspace-backend-api-patterns` for API, worker, and SSE behavior;
- `qa-workspace-ai-generation` for AI pipelines;
- `qa-workspace-testing` for test quality and coverage.

Do not require unrelated improvements outside the reviewed scope.

## Review mindset

Assume the author made reasonable choices until evidence shows otherwise.

For every potential finding, establish:

- the exact changed behavior;
- the condition that triggers the problem;
- the observable consequence;
- whether existing code prevents the problem;
- whether the issue was introduced or materially exposed by this change.

Do not report speculative problems without a plausible execution path.

Prefer a small number of high-confidence findings over a large list of weak
concerns.

## Product invariants

Verify that the change preserves these QA Workspace rules:

- AI proposes; humans decide.
- Generated content is not silently treated as approved.
- Users can inspect AI-generated content before accepting it.
- Approved or manually edited content is not overwritten by regeneration.
- Requirements remain the primary traceability source.
- Test cases remain explicitly traceable to requirements.
- Coverage reflects explicit relationships rather than unsupported AI
  confidence.
- Missing information is exposed rather than invented.
- Important state changes remain explainable and auditable.
- Workspace permissions are enforced by the server.
- Data from one workspace cannot be accessed through another workspace.

Report violations as correctness defects, not product suggestions.

## Review workflow

### 1. Establish the change boundary

Determine:

- what behavior is intentionally changing;
- which users and roles are affected;
- which domain entities are affected;
- which interfaces or contracts are changing;
- whether asynchronous or external operations are involved;
- which behavior must remain unchanged.

Do not infer additional scope that the change does not claim to implement.

### 2. Trace the behavior end to end

Follow relevant data and control flow across:

```text
UI → client validation → API request → authorization → domain logic
→ persistence → background processing → notification → refreshed UI
```

Not every change touches every layer. Inspect only the applicable path.

Look for mismatches between layers, including:

- frontend and backend schema differences;
- missing fields in mapping functions;
- inconsistent enum or status values;
- stale query invalidation;
- incorrect authorization assumptions;
- persisted state not matching returned state;
- events emitted before data is committed;
- migration and ORM model disagreement.

### 3. Evaluate failure paths

Consider realistic failures:

- invalid input;
- unavailable resource;
- forbidden action;
- concurrent update;
- duplicate request;
- background-job retry;
- stale job result;
- provider timeout;
- invalid AI output;
- database failure;
- SSE disconnect;
- partial success.

A missing failure path is a finding only when it can cause incorrect,
misleading, insecure, or unrecoverable behavior.

### 4. Evaluate tests

Check whether tests protect the important behavior introduced or changed.

Do not demand tests for trivial implementation details.

Require tests when they materially protect:

- domain invariants;
- authorization;
- workspace isolation;
- state transitions;
- persistence constraints;
- background-job idempotency;
- regeneration behavior;
- AI-output validation;
- API contracts;
- critical user interactions;
- regression fixes.

### 5. Produce findings

Report findings ordered by severity.

Each finding must identify:

- severity;
- concise problem;
- affected code location;
- triggering scenario;
- user or system impact;
- why existing safeguards do not prevent it.

If no material defects are found, say so directly and mention any remaining
verification limitations.

## Severity model

### P0 — Critical

Immediate release blocker that can cause catastrophic or widespread harm.

Examples:

- cross-workspace data exposure;
- destructive corruption of core production data;
- authentication bypass;
- remote code execution;
- widespread permanent loss of approved artifacts.

Use P0 rarely.

### P1 — High

A serious defect likely to affect users, security, or data integrity.

Examples:

- users can access or mutate another workspace's data;
- regeneration overwrites approved content;
- generated content becomes approved without human action;
- retrying a job creates duplicate accepted artifacts;
- a migration makes existing production data invalid;
- a common workflow is unusable.

### P2 — Medium

A real defect with limited scope, a less common trigger, or a recoverable
impact.

Examples:

- a valid workflow fails for one state or role;
- stale generation results can appear after a newer run;
- a recoverable API error leaves the UI permanently loading;
- an SSE disconnect prevents the UI from learning the final state;
- a field is lost during request or response mapping.

### P3 — Low

A concrete but minor issue with limited impact.

Examples:

- misleading user-visible status;
- inaccessible control blocking keyboard use in a secondary workflow;
- avoidable performance degradation with a demonstrated trigger;
- missing diagnostic information that materially impedes support.

Do not assign severity based on code aesthetics.

## Finding quality

A useful finding is:

- specific;
- reproducible or logically demonstrable;
- attributable to the reviewed change;
- actionable;
- proportionate to its impact.

Prefer:

> **[P1] Scope requirement lookup to the current workspace**  
> The query loads a requirement only by `requirement_id`. A member of workspace
> A can submit an identifier belonging to workspace B and update that
> requirement. The route-level membership check covers only workspace A and
> does not validate ownership of the loaded requirement.

Avoid:

> This query may have security issues.

Keep cited line ranges as small as possible while still showing the problem.

Do not combine unrelated defects into one finding.

## Product and domain review

Verify:

- terminology matches the domain glossary;
- the change does not introduce a second name for an existing concept;
- entity ownership and lifecycle remain explicit;
- state transitions are valid;
- impossible states are prevented where appropriate;
- approved and generated artifacts have distinct state or identity;
- provenance remains available for generated artifacts;
- requirement-to-test relationships are preserved;
- deletion behavior does not leave invalid traceability records;
- assumptions are not persisted as confirmed requirements.

Question a product behavior only when it conflicts with documented context or
the requested outcome.

Do not invent missing requirements to create a review finding.

## Frontend review

For React and TypeScript changes, verify relevant concerns.

### State ownership

Check that:

- server state remains managed through TanStack Query;
- transient UI state remains local when possible;
- URL-addressable state is represented in the URL when appropriate;
- the same state is not duplicated across multiple owners;
- derived state is computed rather than synchronized through effects;
- form state is not unnecessarily copied into global state.

Report state architecture only when it creates an observable correctness or
maintenance problem.

### Data fetching

Check that:

- query keys contain every value affecting the result;
- workspace identity is included where needed;
- mutations invalidate or update all affected queries;
- stale responses cannot replace newer state;
- loading, empty, error, and success states remain distinguishable;
- background progress does not rely solely on a single SSE event;
- retries are appropriate for the operation.

Watch specifically for cache collisions between workspaces.

### Forms and validation

Check that:

- client and server validation do not contradict each other;
- identifiers and ownership come from authoritative context;
- server errors can be presented to the user;
- dirty user input is not overwritten by refetching or generation;
- submission cannot accidentally run twice;
- destructive or irreversible actions require appropriate confirmation.

Client-side validation must not be treated as an authorization boundary.

### Rendering and accessibility

Check that:

- interactive elements use semantic controls;
- keyboard interaction remains possible;
- focus is managed after dialogs and significant async transitions;
- errors are associated with relevant controls;
- generated and approved states are distinguishable without relying only on
  color;
- permission restrictions are understandable in the UI.

Report accessibility issues when they block or materially impair use.

### TypeScript

Look for:

- unsafe assertions hiding invalid runtime data;
- incomplete discriminated-union handling;
- optional fields treated as always present;
- domain types weakened into generic strings;
- transport DTOs used directly where a domain or UI mapping is required;
- duplicated type definitions that can diverge from the contract.

Do not request abstraction only to reduce a small amount of duplication.

## Backend and API review

For FastAPI and Python changes, verify relevant concerns.

### Authorization

Check that every workspace-owned operation verifies:

1. the authenticated user;
2. active membership in the target workspace;
3. permission for the requested action;
4. ownership of every referenced resource.

Do not assume authorization is inherited from the frontend or from possession
of an identifier.

Nested resources must be verified against the same workspace.

### API contracts

Check that:

- request and response schemas match actual behavior;
- status codes and application error codes remain consistent;
- clients can distinguish validation, authorization, conflict, and dependency
  failures;
- newly required fields do not silently break existing clients;
- pagination and ordering are deterministic where required;
- partial objects are not returned as complete resources;
- internal exception details are not exposed.

A successful response should describe committed or clearly provisional state.

### Transactions

Check that:

- related writes are atomic when partial persistence would be invalid;
- external calls do not occur inside long database transactions;
- events are not published before the corresponding transaction commits;
- rollback leaves a recoverable state;
- concurrent transitions cannot create impossible domain state;
- uniqueness conflicts are handled deliberately.

### Async behavior

Check that:

- blocking operations are not executed on the async event loop;
- database sessions do not escape their intended lifetime;
- cancellation does not leave partial state;
- request completion is not incorrectly used as proof of job completion;
- async resources are cleaned up.

Do not flag synchronous code merely because `async` alternatives exist; show
the blocking path and its impact.

## Database and migration review

When schema or persistence changes are present, verify:

- ORM models and migrations agree;
- foreign keys preserve ownership and traceability;
- new non-null fields have a safe migration path;
- uniqueness rules match domain scope;
- indexes support important lookup and authorization paths;
- destructive changes preserve required data;
- backfills are deterministic and safe to rerun when necessary;
- application deployment order is compatible with the migration;
- old and new application versions can coexist when rolling deployment
  requires it.

Pay particular attention to:

- global uniqueness accidentally replacing workspace-scoped uniqueness;
- foreign keys that allow cross-workspace relationships;
- cascade deletion removing approved or auditable content;
- migrations that work only on an empty database;
- constraint creation before existing rows are corrected.

Do not require downgrade support unless the project operationally supports
database downgrades.

## Background-job review

Applies when the change uses or introduces a job or worker system (see
"Infrastructure status"). For AI generation and other jobs, verify:

- the job is persisted before dispatch;
- the payload uses stable identifiers rather than stale object snapshots;
- the worker reloads authoritative state;
- retries are safe;
- duplicate delivery is idempotent;
- terminal state is persisted;
- stale runs cannot overwrite newer results;
- cancellation and completion races are handled;
- workspace ownership is revalidated;
- failures remain visible and auditable;
- notifications occur after persistence.

A queue acknowledging a message does not prove the domain operation completed.

## SSE review

Applies when the change uses or introduces an SSE stream (see "Infrastructure
status"). Verify:

- the stream is authenticated and workspace-authorized;
- events contain stable resource or operation identifiers;
- clients can recover current state through the normal API;
- reconnecting does not require every historical event;
- terminal job states remain persisted independently of SSE;
- disconnects clean up subscriptions and resources;
- database transactions are not held open for the stream lifetime;
- sensitive data is not broadcast to unrelated workspace subscribers.

Treat SSE as a notification channel, not the authoritative store.

## AI-generation review

Applies when the change uses or introduces AI-generation code; no AI provider
is configured by default. Review the full AI boundary:

```text
authorized context → prompt construction → provider call
→ structured parsing → validation → persisted proposal → human review
```

Verify:

- only authorized workspace data enters the prompt;
- secrets and irrelevant sensitive data are excluded;
- prompt and schema versions are recorded where required;
- provider output is treated as untrusted input;
- structured output is validated before persistence;
- referenced domain identifiers are resolved server-side;
- fabricated identifiers cannot create relationships;
- invalid or incomplete output produces a visible failure;
- generated content remains unapproved;
- regeneration creates a new proposal or version;
- approved and manually edited content is preserved;
- stale generation runs cannot win a race against newer runs;
- provenance is sufficient to explain how content was produced.

### Prompt injection

Treat imported requirements and other user-provided text as untrusted data.

Check that such content cannot:

- override system-level generation instructions;
- request secrets or unrelated workspace data;
- invoke tools beyond the intended generation operation;
- bypass structured-output validation;
- cause generated text to be treated as an authorized action.

Do not report generic prompt-injection risk without showing how the reviewed
pipeline gives untrusted content additional authority.

### Model behavior

Do not review natural-language output as if it were deterministic code.

Require deterministic safeguards around model behavior:

- schema validation;
- reference validation;
- permissions;
- state transitions;
- approval boundaries;
- retry limits;
- persistence;
- auditability.

Quality judgments about generated content belong in AI evaluations rather than
ordinary unit tests.

## Security review

Look for concrete instances of:

- broken access control;
- cross-workspace reference injection;
- mass assignment;
- unsafe deserialization;
- SQL injection;
- command injection;
- stored or reflected XSS;
- secret exposure;
- sensitive data in logs;
- insecure direct object references;
- unrestricted file handling;
- missing rate or resource limits on expensive operations;
- server-side request forgery;
- unsafe redirect or URL handling.

Trace input from its source to its sensitive sink before reporting an
injection finding.

Do not assume framework protections without confirming how the relevant API is
used.

Do not request speculative security hardening unrelated to the change.

## Test review

Evaluate whether tests:

- verify behavior rather than implementation details;
- fail if the reviewed defect is introduced;
- cover important negative and authorization paths;
- isolate workspace data;
- use PostgreSQL when database semantics matter;
- control time, randomness, jobs, and external providers;
- verify persisted results for async operations;
- avoid arbitrary sleeps;
- avoid live AI calls in deterministic CI;
- preserve readability and independence.

Passing tests do not prove correctness if assertions miss the risky behavior.

For a bug fix, expect a regression test at the narrowest reliable layer when
feasible.

## Compatibility review

Check compatibility when the change affects:

- API request or response schemas;
- stored data;
- background-job payloads;
- SSE event shapes;
- environment configuration;
- feature flags;
- public URLs;
- query keys or persisted frontend state.

Identify whether producers and consumers can be deployed independently.

Report compatibility issues only when the repository or deployment model makes
mixed versions plausible.

## Performance review

Report performance findings only when there is a concrete scale or execution
path.

Relevant risks include:

- N+1 database queries on collections;
- unbounded result sets;
- missing pagination;
- repeated expensive AI calls;
- duplicate background jobs;
- blocking I/O on the event loop;
- unnecessary full-cache invalidation causing repeated network work;
- rendering large collections without appropriate limits;
- holding database connections for SSE lifetime.

Do not report micro-optimizations without measurable or logically significant
impact.

## Review boundaries

A review does not authorize code modification.

Unless the user explicitly requests fixes:

- inspect;
- reason;
- run safe verification when useful;
- report findings;
- do not edit files;
- do not create commits;
- do not change pull requests.

Do not expand the review into an architecture redesign.

Mention optional improvements separately only if they materially reduce a
demonstrated risk. Do not mix them with correctness findings.

## Output format

Lead with findings ordered from highest to lowest severity.

Use this format for each finding:

```markdown
### [P1] Concise imperative or problem statement

`path/to/file.py:42`

Explain the triggering scenario, the resulting behavior, and why this change
allows it. Keep the explanation focused on the defect and its impact.
```

After findings, include only relevant sections:

### Open questions

Include questions only when missing context prevents determining whether
behavior is correct.

### Verification gaps

State checks that could not be completed, such as unavailable tests,
environment dependencies, or missing migration history.

### Summary

Provide a brief overall assessment after the findings.

If no findings are present, state:

```text
No material correctness issues found.
```

Then mention remaining verification gaps, if any.

Do not bury findings beneath a general summary.

## Prohibited behavior

Do not:

- report personal style preferences as defects;
- require unrelated refactoring;
- invent undocumented product requirements;
- report a hypothetical issue without a plausible trigger;
- flag pre-existing code unless the change materially exposes or worsens it;
- assume frontend permission checks provide security;
- assume passing tests prove the implementation is correct;
- treat AI output as trusted;
- treat generated content as approved;
- ignore workspace ownership on nested resources;
- recommend arbitrary retries for non-idempotent operations;
- require 100% test coverage;
- request abstractions without a concrete benefit;
- combine unrelated issues into one finding;
- exaggerate severity;
- claim verification that was not performed;
- modify code unless the user explicitly asks for fixes.