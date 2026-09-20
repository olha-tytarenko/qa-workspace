---
name: qa-workspace-frontend-patterns
description: >
  Apply QA Workspace frontend architecture and implementation patterns when
  creating or changing React components, routes, forms, client state, server
  state, API integrations, async AI workflows, user interactions, styling,
  accessibility, or frontend performance. Use for frontend implementation and
  review in the React and TypeScript application. Do not use for backend-only
  work, product analysis without UI changes, or domain modeling that does not
  affect the frontend.
---

# QA Workspace Frontend Patterns

Build QA Workspace frontend functionality using React, TypeScript, Vite,
TanStack Query, React Router, React Hook Form, and Zod.

Prefer explicit data flow, clear ownership, accessible interactions, and
feature-local organization over premature abstraction.

Preserve the distinction between AI-generated suggestions, human edits, review
decisions, and approved artifacts in every relevant interface.

## Inspect before implementing

Before creating or modifying frontend code:

1. Read the relevant product requirements and acceptance criteria.
2. Apply `qa-workspace-product-context` when behavior or terminology is
   involved.
3. Apply `qa-workspace-evolve-domain-model` when changing domain-facing types,
   states, or transitions.
4. Inspect the existing route, feature module, shared components, hooks, API
   layer, and tests.
5. Find the closest comparable implementation.
6. Identify the source and owner of each required piece of state.
7. Identify loading, empty, error, permission, and stale-data behavior.
8. Search for existing components before creating new ones.

Follow established repository patterns unless they conflict with explicit
requirements, accessibility, correctness, or product invariants.

## Organize by product feature

Group product-specific code by feature or domain capability rather than by
technical file type.

A feature module may contain:

```text
features/
└── requirements/
    ├── api/
    ├── components/
    ├── hooks/
    ├── model/
    ├── routes/
    ├── schemas/
    └── tests/
```

Adapt the exact structure to the existing repository. Do not create empty
directories or layers without current use.

Keep code close to the feature that owns it.

Move code into shared modules only when:

- it is already used by multiple features;
- its responsibility is genuinely domain-independent;
- sharing does not require feature-specific conditions;
- its API can remain smaller and clearer than duplicated implementations.

Do not use `shared`, `common`, or `utils` as dumping grounds for unrelated
logic.

## Define dependency direction

Prefer this dependency direction:

```text
application shell
    ↓
routes
    ↓
feature modules
    ↓
shared UI and infrastructure
```

Shared modules must not import from feature modules.

A feature may depend on shared UI, API infrastructure, and shared utilities.
One feature should not import another feature's internal files.

When features need to coordinate, use:

- an explicit public feature API;
- a shared domain contract;
- route composition;
- an application-level orchestration layer.

Avoid circular dependencies and deep imports into another module's internals.

## Design components around responsibility

Create a component when it has a distinct responsibility, meaningful behavior,
or reusable visual structure.

Keep a component focused on one primary concern.

Split a component when:

- separate parts change for different reasons;
- a section has independent state or behavior;
- a section can be named as a meaningful UI concept;
- testing the parent requires excessive setup;
- conditionals make the main user flow difficult to understand.

Do not split components solely to reduce line count.

Do not create wrapper components that only rename an existing component
without adding semantics, behavior, accessibility, or styling constraints.

Prefer composition over large components controlled by many boolean props.

Avoid APIs such as:

```tsx
<ArtifactCard
  isRequirement
  isGenerated
  isEditable
  isReviewMode
  isCompact
/>
```

Prefer explicit variants or composed subcomponents when the behaviors are
meaningfully different.

## Separate orchestration from presentation

Route and feature-level components may:

- read route parameters;
- call query and mutation hooks;
- coordinate loading and error states;
- enforce permission-aware behavior;
- map domain data into UI props;
- connect user actions to application operations.

Presentational components should primarily:

- receive explicit props;
- render accessible UI;
- emit semantic user actions;
- avoid fetching unrelated data;
- avoid knowing API transport details.

Do not force strict container/presentation separation when it adds indirection
without improving ownership or testability.

## Keep rendering pure

Treat React components as pure rendering functions.

During render, do not:

- mutate props or external state;
- start network requests;
- write to storage;
- subscribe to external systems;
- trigger navigation;
- update another component;
- derive random or time-dependent persistent values.

Perform external synchronization in event handlers, query or mutation
functions, or effects with explicit dependencies.

Do not use an effect to compute data that can be derived during render.

Do not use an effect to respond to a user action when the action handler already
has the required context.

## Use the minimum necessary state

Store only information that must be remembered between renders.

Do not store values that can be calculated from:

- props;
- query data;
- route state;
- form state;
- other local state.

Avoid duplicated and contradictory state.

Prefer:

```text
requirements + activeFilter
```

over:

```text
requirements + activeFilter + filteredRequirements
```

Compute `filteredRequirements` from the source data and filter.

Keep related state together when it changes as one unit. Keep unrelated state
separate.

Avoid independent booleans that permit impossible UI states. Prefer explicit
unions or state values.

For example, prefer:

```ts
type GenerationStatus =
  | 'idle'
  | 'queued'
  | 'processing'
  | 'completed'
  | 'failed';
```

over several independent flags such as `isQueued`, `isProcessing`,
`isCompleted`, and `hasFailed`.

## Assign state ownership

Use the narrowest appropriate owner for each type of state.

### Local component state

Use local React state for transient interaction state owned by one component
or a small subtree, such as:

- an open menu;
- the active tab when it is not URL-addressable;
- temporary expansion state;
- a local confirmation dialog;
- unsaved UI-only input.

### Form state

Use React Hook Form for editable form values, validation state, dirty state,
and submission state.

Do not copy form fields into a separate React state store.

### Server state

Use TanStack Query for data owned by the server, including:

- workspaces;
- projects;
- features;
- requirements;
- analyses;
- test cases;
- coverage data;
- generation-run status.

Do not copy query results into global client state merely to make them
available in multiple components.

### URL state

Use React Router search parameters or route parameters for state that should
survive refreshes, support deep links, or participate in browser navigation,
such as:

- selected workspace, project, or feature;
- active artifact identifier;
- shareable filters;
- pagination;
- sorting;
- view mode when it is meaningful in a copied URL.

Do not place sensitive or large serialized objects in the URL.

### Shared client state

Introduce shared client state only for client-owned information that:

- is required by distant parts of the application;
- cannot be derived from server or URL state;
- has a clear owner and lifecycle.

Do not introduce a global store for data already managed by TanStack Query,
React Router, or React Hook Form.

## Preserve one source of truth

For each value, identify one authoritative source.

Avoid synchronization between multiple state containers when one can derive
the required value from another.

Do not maintain the same server entity independently in:

- TanStack Query cache;
- component state;
- a global store;
- form state.

A form may initialize from server data and then own an editable draft. Treat
the form draft and persisted server entity as distinct states.

When the server entity changes while a form is dirty, do not reset or overwrite
the form silently.

## Use TanStack Query intentionally

Create query keys that reflect stable domain identity and scope.

Include relevant ownership identifiers in query keys, such as workspace,
project, feature, and artifact identifiers.

Centralize query-key construction when multiple hooks must invalidate or
update the same data.

Configure `staleTime`, retries, refetch behavior, and cache lifetime according
to actual product behavior rather than relying on defaults accidentally.

After a mutation:

- invalidate or update only affected queries;
- preserve unrelated cached data;
- reconcile the authoritative server response;
- expose mutation failures to the user;
- prevent stale responses from replacing newer state.

Do not manually fetch server data in effects when TanStack Query already owns
that lifecycle.

Do not use a mutation for read-only operations merely because they are manually
triggered. Use a disabled or parameterized query when caching and deduplication
remain useful.

## Use optimistic updates selectively

Use optimistic updates only when:

- the action is reversible;
- the expected server result is predictable;
- rollback can restore the previous state;
- temporary inconsistency is acceptable;
- failure is clearly communicated.

Avoid optimistic approval, rejection, permission changes, destructive actions,
and workflow transitions whose success depends on server-side invariants.

For approval and review decisions, prefer displaying an explicit pending state
until the server confirms the transition.

When using an optimistic update:

1. Cancel relevant in-flight queries.
2. Snapshot the previous cache state.
3. Apply the optimistic value.
4. Restore the snapshot on failure.
5. Reconcile with the server response.
6. Invalidate affected queries when necessary.

## Separate transport and UI models

Do not expose raw API response shapes throughout the component tree.

Use explicit boundaries where transport and UI responsibilities differ:

```text
API response DTO
    ↓ validation or decoding
domain-facing frontend model
    ↓ selector or mapper when needed
component props
```

Use a mapper when it:

- converts serialized values;
- normalizes nullable or optional fields;
- creates discriminated unions;
- adapts backend naming;
- combines values for a stable UI contract;
- prevents transport concerns from leaking into components.

Do not add a mapper that only copies identical fields without enforcing a
meaningful boundary.

Do not silently replace missing required data with plausible defaults. Surface
invalid or incomplete data explicitly.

## Use TypeScript to model valid states

Prefer discriminated unions for mutually exclusive states and variants.

Use domain-specific identifiers when mixing identifiers would create realistic
risk.

Avoid:

- `any`;
- broad type assertions;
- non-null assertions without a proven invariant;
- unvalidated casts of API or AI output;
- boolean flags that create invalid combinations;
- catch-all string types for known status values.

Narrow unknown external data before use.

Keep component props smaller than the complete domain object when the component
needs only part of it.

Do not weaken a domain type merely to accommodate temporary loading or form
state. Model those states separately.

## Build forms with React Hook Form and Zod

Use React Hook Form to manage form interaction and Zod to validate input
structure and constraints.

Keep validation rules aligned with backend and domain rules without assuming
frontend validation is authoritative.

Distinguish:

- field validation;
- cross-field validation;
- server validation;
- domain invariant failures;
- authorization failures.

Display validation feedback close to the relevant field and provide a
form-level summary when errors affect the entire operation.

Preserve user input after failed submission.

Do not clear or reset a form until the server confirms success.

Warn before discarding meaningful unsaved changes when navigation can cause
data loss.

Do not infer approval from submitting an edit form. Editing and approval are
separate product actions.

## Represent async AI workflows explicitly

AI generation may continue beyond the initiating request.

Model generation as a server-owned job with explicit states:

```text
queued → processing → completed
                    → failed
```

Use the confirmed backend transport, such as SSE, to receive progress or
completion updates.

The UI must:

- show that generation has started;
- distinguish queued from processing;
- avoid presenting partial output as approved content;
- handle connection loss;
- recover by refetching authoritative job state;
- expose failure and retry behavior;
- prevent an older generation result from replacing a newer one;
- preserve user edits and approved artifacts during regeneration.

Treat streamed events as notifications that state may have changed, not
necessarily as the sole durable source of truth.

After reconnecting or receiving a terminal event, refetch authoritative server
state when required.

Clean up subscriptions when the owning route or component unmounts.

## Model complete UI states

For every data-backed screen or component, handle the relevant:

- initial loading state;
- background refresh state;
- empty state;
- success state;
- partial-data state;
- validation failure;
- permission failure;
- recoverable server or network failure;
- unrecoverable failure.

Do not render an empty state while the initial request is still loading.

Do not replace usable stale data with a full-screen loading state during a
background refresh.

Keep errors local to the failed boundary when the rest of the screen remains
usable.

Provide a retry action when retrying is meaningful.

Use an error boundary for unexpected rendering failures, not ordinary API
validation errors.

## Make AI and review states visible

Users must be able to distinguish:

- human-created content;
- AI-generated suggestions;
- AI-generated content edited by a human;
- content awaiting review;
- approved artifacts;
- rejected suggestions;
- generation in progress;
- generation failure.

Do not communicate these distinctions through color alone.

Use explicit labels, status text, icons with accessible names, or grouped
actions.

Keep approval and rejection controls visually and semantically distinct from
ordinary editing and saving.

Do not make a generated suggestion visually indistinguishable from an approved
artifact.

## Build accessible interactions

Use semantic HTML before adding ARIA.

Use native elements for their intended behavior:

- `button` for actions;
- `a` for navigation;
- `label` associated with each form control;
- headings in a logical hierarchy;
- lists and tables for genuinely tabular or list content.

Ensure all interactive behavior is operable with a keyboard.

Provide visible focus indicators.

Manage focus deliberately when:

- opening or closing a modal;
- showing a blocking validation error;
- adding dynamic content that requires immediate attention;
- completing an action that removes the focused element.

Return focus to a sensible location after dialogs close.

Use `aria-live` sparingly for meaningful asynchronous status updates, such as
generation completion or failure.

Do not announce frequent progress events that would overwhelm assistive
technology.

Do not use placeholder text as the only label.

Do not add ARIA when native HTML already provides the required semantics.

## Use the design system first

Before creating a UI primitive:

1. Search the existing component library.
2. Check whether an existing component supports the required behavior.
3. Extend it when the responsibility remains coherent.
4. Create a new primitive only when no suitable component exists.

Use existing design tokens for:

- color;
- typography;
- spacing;
- radius;
- shadows;
- motion;
- focus styles;
- breakpoints.

Do not introduce arbitrary visual values when an appropriate token exists.

Do not fork an existing component solely for a one-screen visual difference.
Prefer variants or composition when the behavior remains consistent.

Keep product-specific semantics in feature components rather than embedding
them into generic primitives.

## Design responsive layouts intentionally

QA Workspace is desktop-first, but critical workflows must remain usable at
supported smaller widths.

Prefer layouts that adapt through normal document flow, flexible grids, and
content-driven constraints.

Avoid fixed dimensions for content that may contain generated or user-authored
text.

Test long requirements, test steps, error messages, and translated content.

Do not hide essential review or approval actions solely because the viewport is
smaller.

When complex tables cannot remain usable on narrow screens, provide a deliberate
alternative such as horizontal scrolling or a structured card view.

## Optimize performance from evidence

Write clear code first. Optimize when profiling, measurements, or an obvious
high-cost operation justifies it.

Do not add `React.memo`, `useMemo`, or `useCallback` by default.

Use memoization when:

- an identified calculation is meaningfully expensive;
- a stable reference is required by a memoized child or external API;
- profiling shows avoidable repeated rendering;
- a dependency requires referential stability.

Do not use memoization to hide incorrect state ownership or effect
dependencies.

Keep state close to where it is used to reduce unnecessary render scope.

For large collections, consider pagination or virtualization only when actual
data size makes full rendering expensive.

Lazy-load route-level or genuinely heavy functionality when it reduces initial
work without harming the primary workflow.

Avoid creating a separate network request in every repeated row when data can
be fetched or composed at a higher boundary.

## Handle destructive actions carefully

Require clear confirmation for actions that are difficult to reverse or that
remove meaningful user work.

The confirmation must identify the affected resource and consequence.

Do not use optimistic removal for destructive actions unless reliable recovery
exists.

Disable repeated submission while the same destructive operation is pending.

After deletion, navigate to a valid location and restore focus appropriately.

Do not use browser confirmation dialogs when the application requires richer
context or accessible custom behavior.

## Test user-observable behavior

Add frontend tests for behavior introduced or changed by the implementation.

Prefer tests that interact through accessible roles, labels, and visible text.

Test the relevant:

- successful user flow;
- validation behavior;
- loading and error behavior;
- permission-aware behavior;
- review and approval separation;
- preservation of edits during regeneration;
- stale-generation protection;
- keyboard interaction;
- regression scenario for a bug fix.

Mock the network boundary rather than mocking internal hooks or component
implementation details when practical.

Do not assert internal state, hook calls, or CSS class names unless they are
the actual contract under test.

Use the repository's dedicated testing skill for detailed test strategy when
available.

## Review frontend changes

Before completing frontend work, verify:

- components use established feature boundaries;
- server data remains in TanStack Query;
- form data remains in React Hook Form;
- URL-worthy state is represented in the route;
- derived values are not duplicated in state;
- loading, empty, error, and permission states are distinguishable;
- AI suggestions are distinct from approved artifacts;
- approval is an explicit action;
- regeneration cannot silently replace user work;
- keyboard and focus behavior work;
- API data is validated or mapped at the appropriate boundary;
- memoization has a specific justification;
- no existing component has been duplicated;
- affected tests, type checks, linting, and builds pass.

Do not claim accessibility or performance has been verified if it was not
actually checked.
