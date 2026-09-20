---
name: qa-workspace-implement-feature
description: >
  Implement new QA Workspace functionality or change existing product behavior
  from requirements through verified code. Use for end-to-end features,
  workflow changes, user-visible behavior, API-backed functionality, and
  product bug fixes that require code changes. Do not use for product analysis
  without implementation, purely mechanical refactoring, dependency updates,
  formatting-only changes, or documentation-only work.
---

# Implement a QA Workspace Feature

Implement the smallest coherent change that satisfies the confirmed
requirements, preserves existing behavior, and can be reviewed independently.

Do not commit changes unless the user explicitly asks for a commit.

## Establish context

Before changing code:

1. Read the user request and any supplied requirements or acceptance criteria.
2. Inspect the repository instructions and relevant package scripts.
3. Find the current implementation and the nearest comparable feature.
4. Identify the affected UI, domain, API, persistence, and test boundaries.
5. Determine whether the task changes product behavior or domain semantics.
6. Apply `qa-workspace-product-context` when product judgment is required.
7. Apply more specific architecture or testing skills when they are available.

Treat the existing repository as evidence, not as automatically correct.
Follow established patterns unless they conflict with explicit requirements,
product invariants, security, or correctness.

## Separate facts from assumptions

Before implementation, distinguish:

- confirmed behavior from the request or product documentation;
- behavior demonstrated by the existing code;
- assumptions required to proceed;
- unresolved questions that could materially change the solution.

Ask for clarification before implementing when uncertainty affects:

- permissions or workspace isolation;
- destructive or irreversible behavior;
- approval and review semantics;
- persistence or migration behavior;
- public API contracts;
- ownership of domain entities;
- replacement of approved or user-edited content.

For reversible implementation details, choose the simplest option consistent
with existing patterns and state the assumption when it matters.

Continue with unaffected work when one part of the task is blocked.

## Define the implementation boundary

Express the task as the smallest end-to-end user outcome.

Before editing, identify:

- the behavior being added or changed;
- the relevant entry point;
- the data that enters the system;
- the state transitions involved;
- the observable successful result;
- expected loading, empty, error, and permission states;
- behavior that must remain unchanged;
- work explicitly outside the current scope.

Do not expand the task with speculative extensibility or unrelated cleanup.

If the requested change is too large for a safe review, split it into
independently valid slices. Each slice must leave the application in a working
state and include its relevant tests.

## Inspect before designing

Search the codebase before introducing a new:

- component;
- hook;
- domain type;
- API abstraction;
- state container;
- validation schema;
- utility;
- error representation;
- test helper.

Prefer extending an existing abstraction when the new responsibility remains
coherent.

Create a new abstraction when reuse would introduce unrelated conditionals,
weaken type safety, or combine distinct domain responsibilities.

Do not copy an existing implementation merely to avoid understanding it.

## Plan non-trivial changes

Create a short implementation plan when the task:

- crosses multiple architectural boundaries;
- changes persisted data;
- affects permissions or approval workflows;
- changes a public API contract;
- requires a migration;
- has multiple independently verifiable steps.

Keep the plan outcome-oriented. Do not list obvious file-editing operations.

Update the plan when repository evidence invalidates an assumption.

Skip a formal plan for small, localized changes whose implementation and
verification are already clear.

## Implement a vertical slice

Prefer a vertical slice that delivers one complete user-visible behavior over
several disconnected infrastructure changes.

When relevant, implement in this order:

1. Establish or update the domain behavior.
2. Define or update the boundary contract.
3. Implement persistence or external integration.
4. Connect application state and orchestration.
5. Implement the user interaction.
6. Add automated verification.
7. Verify the completed behavior.

This order is guidance, not a required architectural layering scheme. Adapt it
to the repository structure.

Keep the application functional after each coherent change.

## Preserve product behavior

When changing QA Workspace functionality:

- preserve the distinction between AI-generated suggestions and approved
  artifacts;
- do not infer approval from viewing or editing content;
- do not silently overwrite approved artifacts or unreviewed user edits;
- preserve traceability between test cases and requirements;
- preserve workspace and project ownership boundaries;
- expose missing information rather than inventing product behavior;
- retain provenance when AI-generated content is edited or approved.

If the requested implementation conflicts with a product invariant, stop the
affected work and explain the conflict.

## Preserve contracts deliberately

Treat the following as contracts:

- public APIs;
- persisted schemas;
- URL structures;
- serialized data;
- domain identifiers;
- status values;
- permissions;
- events consumed outside the changed module.

Do not change a contract merely to simplify the local implementation.

When a contract change is necessary:

1. Identify its consumers.
2. Determine whether backward compatibility is required.
3. Update affected consumers in the same coherent change when possible.
4. Add migration or compatibility handling where necessary.
5. Document any remaining rollout dependency.

Do not add compatibility layers without an identified consumer.

## Handle failures explicitly

For each external or asynchronous operation, account for:

- loading;
- success;
- empty results;
- expected validation failures;
- authorization failures;
- server or network failures;
- stale or superseded requests;
- retries or repeated submissions where relevant.

Avoid swallowing errors or representing failures as successful empty results.

Prevent stale asynchronous results from replacing newer state when the
interaction can produce overlapping requests.

Do not add retries to non-idempotent operations unless duplicate execution is
handled safely.

## Keep changes reviewable

Keep the change focused on one coherent outcome.

Avoid:

- unrelated refactoring;
- opportunistic renaming across the repository;
- new abstractions without an immediate use;
- broad formatting changes;
- duplicated domain rules;
- hidden behavior changes;
- generated code changes without verifying their source and output.

Include enough context in names, tests, and the final summary for another
engineer to understand the change without reconstructing the entire task.

## Add proportionate tests

Add or update tests for behavior introduced or changed by the feature.

At minimum, cover:

- the primary successful path;
- material validation or failure behavior;
- permission boundaries when affected;
- preservation of approved or user-edited content when affected;
- the regression scenario for a bug fix.

Test observable behavior and domain outcomes rather than implementation
details.

Use the repository's existing testing strategy and helpers. Do not introduce a
new testing framework for a single feature.

If an appropriate testing layer does not exist, explain the limitation and add
the highest-value verification that fits the current repository.

Do not treat generated tests as trustworthy merely because they pass. Review
their assertions and confirm that they can fail when the behavior is wrong.

## Validate the implementation

Use the narrowest relevant checks during implementation, then run the broader
available checks before completion.

When supported by the repository, verify:

1. affected tests;
2. static type checking;
3. linting;
4. the relevant package or application build;
5. broader tests when the change could affect shared behavior.

Also inspect the final diff for:

- unintended files;
- temporary debugging code;
- accidental formatting changes;
- exposed secrets;
- weakened types;
- incomplete error handling;
- missing cleanup;
- unrelated dependency or lockfile changes.

Do not claim a check passed unless it was actually executed successfully.

If a check cannot run, report:

- the exact check;
- why it could not run;
- what was verified instead;
- the remaining risk.

## Review before handoff

Before declaring the task complete, confirm that:

- the implementation satisfies the requested outcome;
- product invariants remain intact;
- workspace boundaries and permissions are preserved;
- new behavior is reachable through the intended user flow;
- error and empty states are handled where relevant;
- tests verify meaningful behavior;
- no unrelated scope was introduced;
- the final diff contains only intended changes.

Do not commit or publish the implementation without explicit user instruction.

## Report the result

Keep the final report concise and include:

- what user-visible behavior was implemented;
- the important implementation decisions;
- verification that was executed;
- any unresolved limitation or follow-up that materially affects the result.

Do not include a file-by-file narration unless the user requests it.