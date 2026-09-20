---
name: qa-workspace-evolve-domain-model
description: >
  Design, review, or change the QA Workspace domain model. Use when adding or
  modifying domain entities, value objects, relationships, ownership
  boundaries, lifecycle states, state transitions, invariants, identifiers,
  persistence semantics, or domain-facing API contracts. Use for schema
  changes that affect business meaning. Do not use for UI-only types,
  transport-only DTO changes, database optimization without semantic changes,
  or mechanical refactoring that preserves the domain model.
---

# Evolve the QA Workspace Domain Model

Model QA Workspace concepts according to their business meaning, ownership,
lifecycle, and invariants.

Keep the domain model independent from UI components, transport formats, ORM
limitations, and temporary implementation details.

## Load domain context

Before making a domain decision:

1. Apply `qa-workspace-product-context`.
2. Read its `product.md` and `domain-glossary.md`.
3. Inspect the existing domain types, persistence schema, API contracts, and
   related tests.
4. Identify the current behavior before proposing a replacement.
5. Use the terminology defined in the glossary consistently.

Treat the glossary as the source of domain language, not as a complete database
schema or class diagram.

If the code and glossary disagree, surface the discrepancy. Do not silently
change one to match the other.

## Start from behavior

Before adding or modifying a domain concept, identify:

- the business concept being represented;
- why it needs independent representation;
- who owns it;
- which operations affect it;
- which rules must always remain true;
- whether it has identity and lifecycle;
- which other concepts it references;
- which changes must be consistent together;
- whether its history or provenance matters.

Do not begin by designing tables, DTOs, endpoints, or React types.

## Classify domain concepts

Classify each concept according to its domain role.

### Entity

Use an entity when the concept:

- has stable identity;
- changes over time;
- must be referenced independently;
- has a lifecycle that matters to the product.

Examples may include:

- Workspace;
- Project;
- Feature;
- Requirement;
- Acceptance Criterion;
- Test Case;
- Generation Run.

Do not create an entity solely because a database table is convenient.

### Value object

Use a value object when the concept:

- is defined by its values rather than identity;
- has no independent lifecycle;
- can be replaced as a whole;
- benefits from centralized validation.

Possible examples include:

- structured test data;
- expected result;
- provenance metadata;
- analysis configuration.

Do not assign identity to a value object unless the product needs to reference,
review, version, or update it independently.

### Relationship

Represent a relationship explicitly when the relationship itself has domain
meaning, lifecycle, metadata, provenance, or review state.

For example, model a coverage link explicitly if the system must preserve:

- who or what proposed the link;
- whether a human confirmed it;
- when it was created;
- which part of a requirement is covered.

Do not create a separate relationship entity for a simple foreign key with no
independent behavior or metadata.

### Domain service

Use a domain service only when domain behavior:

- spans multiple entities or aggregates;
- does not naturally belong to one entity;
- expresses a meaningful domain operation.

Do not move entity invariants into generic service classes merely to keep
entities as passive data containers.

## Define ownership boundaries

Every persisted domain entity must have a clear ownership path.

Use the initial hierarchy:

```text
Workspace
└── Project
    └── Feature
        ├── Requirement
        │   ├── Acceptance Criterion
        │   └── Coverage Link
        ├── Test Case
        ├── Requirement Analysis
        │   ├── Finding
        │   └── Clarification Question
        └── Generation Run
```

Treat this hierarchy as a conceptual ownership model, not a requirement to use
nested storage or a single aggregate.

A `Coverage Link` belongs to the feature context and connects a test case with
a requirement from that same feature unless cross-feature traceability is
explicitly introduced.

Do not allow a child entity to reference an owner from another workspace.

## Protect the workspace boundary

Treat `Workspace` as the top-level authorization and data-isolation boundary.

For every workspace-owned operation:

1. Establish the active workspace.
2. Resolve the target entity through its ownership path.
3. Verify membership and permission within that workspace.
4. Reject cross-workspace references.
5. Avoid authorizing access solely because the caller knows an entity ID.

Do not accept a client-provided `workspaceId` as proof of ownership.

When creating relationships, verify that both referenced entities belong to
the same permitted workspace and expected parent context.

## Define aggregate boundaries deliberately

Group entities into an aggregate only when they must remain consistent within
the same business operation.

Use transaction and consistency requirements to identify an aggregate
boundary, not containment alone.

Prefer small aggregates.

Reference entities in different aggregates by identity rather than by loading
and mutating an entire object graph.

Do not assume that `Feature` and every artifact beneath it form one aggregate.
That boundary would create unnecessary contention and oversized updates.

Potential aggregate roots may include:

- Feature;
- Requirement;
- Test Case;
- Requirement Analysis;
- Generation Run.

Confirm aggregate boundaries from actual operations and consistency rules
before encoding them.

## Keep invariants close to the model

Express domain rules at the narrowest layer capable of enforcing them
consistently.

Important QA Workspace invariants include:

- a project belongs to one workspace;
- a feature belongs to one project;
- a requirement belongs to one feature;
- an acceptance criterion is derived from at least one requirement;
- a test case is traceable to at least one requirement;
- a coverage link connects a test case and requirement from the same feature;
- AI-generated suggestions are not approved automatically;
- editing a suggestion does not imply approval;
- an approved artifact is created through an explicit human decision;
- regeneration does not overwrite approved artifacts;
- regeneration does not overwrite unreviewed user edits;
- provenance remains available after editing or approval;
- cross-workspace relationships are invalid.

Do not rely on UI controls alone to enforce these rules.

Apply important invariants at the domain or application boundary and support
them with database constraints when practical.

## Model state explicitly

Use explicit lifecycle states when valid operations depend on the current
state.

Avoid combinations of independent booleans that can create impossible states,
such as:

```text
isDraft = true
isApproved = true
isRejected = true
```

Prefer a single state with defined transitions.

A provisional artifact lifecycle may include:

```text
draft → in_review → approved
                  → rejected
```

Do not treat this provisional lifecycle as final when product requirements
need additional states.

For every lifecycle, define:

- valid states;
- initial state;
- allowed transitions;
- actor permitted to perform each transition;
- required preconditions;
- resulting side effects;
- whether the transition is reversible.

Reject invalid transitions rather than silently normalizing them.

## Separate status from provenance

Model lifecycle status and content provenance as independent concerns.

Status describes the current workflow state:

```text
draft
in_review
approved
rejected
```

Provenance describes how the content originated:

```text
human_created
ai_generated
ai_generated_human_edited
```

An AI-generated artifact may become approved while retaining AI-generated
provenance.

Do not encode provenance through status names such as
`approved_ai_generated`.

Do not infer provenance solely by comparing content.

## Model review explicitly

Treat review as an explicit user action.

Do not infer acceptance or approval from:

- opening an artifact;
- editing content;
- saving a draft;
- navigating away;
- executing regeneration;
- using generated content as a starting point.

Preserve the information necessary to determine:

- which artifact or suggestion was reviewed;
- which user made the decision;
- what decision was made;
- when the decision occurred;
- which version of the content was reviewed.

If editing approved content invalidates approval, require that behavior to be
an explicit product decision. Do not assume it silently.

## Preserve identity

Use stable, opaque identifiers for independently referenced entities.

Do not derive permanent identity from:

- display names;
- titles;
- array positions;
- mutable slugs;
- generated text;
- parent ordering.

Keep identity stable across ordinary edits.

When duplicating an entity, create a new identity and preserve source
provenance separately if the relationship matters.

## Separate domain models from boundary models

Do not use one type as all of the following:

- persistence record;
- API request;
- API response;
- domain entity;
- frontend state;
- form state;
- rendered view model.

Use explicit transformations at boundaries when the representations have
different responsibilities.

A transport DTO may contain optional, serialized, or backward-compatible
fields that should not weaken domain invariants.

A persistence record may contain storage-specific values that should not leak
into domain behavior.

A UI model may combine or derive information for presentation without becoming
the source of domain truth.

Avoid mapping layers that merely copy identical properties without creating a
meaningful boundary.

## Model AI output as untrusted input

Treat model output as external, untrusted data.

Before creating domain objects from AI output:

1. Validate the structural schema.
2. Validate referenced entity identifiers.
3. Verify workspace and feature ownership.
4. Validate allowed enum and status values.
5. Apply domain invariants.
6. Preserve generation provenance.
7. Store the result as a suggestion rather than an approved artifact.

Schema validation proves shape, not factual correctness or product approval.

Do not allow generated output to choose permissions, approval state, ownership,
or authoritative identifiers.

## Model generation runs separately

Use a `Generation Run` to represent an execution of an AI operation when the
product needs reproducibility, provenance, status, or multiple generations.

A generation run may preserve:

- operation type;
- source entity identifiers;
- relevant input snapshot or version;
- model and prompt version when available;
- execution status;
- generated suggestions;
- timestamps;
- failure information.

Do not store only the latest generated output if regeneration history is a
product requirement.

Do not overwrite approved artifacts when recording a new generation.

## Handle concurrent changes

Identify operations where two users or background processes may update the same
artifact.

Protect against silent lost updates when:

- a user edits content while regeneration runs;
- two users review the same artifact;
- approval occurs while another version is being edited;
- a coverage link is changed concurrently;
- a stale client submits an older representation.

Use the repository's established concurrency mechanism when one exists.

Otherwise, prefer explicit version checks or optimistic concurrency for
artifacts whose reviewed content must not be overwritten.

Do not add concurrency infrastructure to simple append-only operations without
an identified race.

## Evolve persisted models safely

Before changing persisted data:

1. Identify existing records affected by the change.
2. Decide how old records map to the new model.
3. Determine whether the migration is reversible.
4. Preserve data required by existing consumers.
5. Update domain validation and persistence constraints together.
6. Verify both newly created and migrated records.
7. Account for deployments where old and new code may temporarily coexist.

Do not make an existing required field non-nullable without a valid migration
or default derived from domain rules.

Do not invent domain data merely to satisfy a database constraint.

Prefer additive changes when backward compatibility is required.

## Evolve API contracts deliberately

When a domain change affects an API:

- expose resources and operations using domain language;
- preserve stable identifiers;
- validate ownership server-side;
- distinguish omission from explicitly setting a nullable value;
- avoid exposing persistence implementation details;
- return invalid transition and invariant failures as explicit errors;
- update consumers or provide compatibility handling.

Do not expose unrestricted generic updates for fields controlled by domain
transitions.

For example, prefer an explicit approval operation over allowing a client to
set `status: "approved"` through an arbitrary patch request.

## Validate a domain change

Add or update tests for:

- creation with valid data;
- invariant violations;
- allowed state transitions;
- rejected state transitions;
- ownership boundaries;
- cross-workspace references;
- AI-generated content remaining unapproved;
- preservation of approved content during regeneration;
- provenance preservation;
- migration of existing data when applicable;
- concurrent update protection when applicable.

Test domain outcomes rather than ORM or framework implementation details.

Verify database constraints separately when they are part of the protection.

## Communicate domain decisions

When asked to propose or review a domain change, describe only the relevant:

- domain concepts;
- identities;
- ownership relationships;
- aggregate or consistency boundaries;
- invariants;
- lifecycle states and transitions;
- authorization implications;
- persistence implications;
- API implications;
- migration requirements;
- unresolved product questions.

Do not produce a complete domain redesign when the task concerns one bounded
change.

## Avoid premature complexity

Do not introduce:

- microservices solely to enforce domain boundaries;
- event sourcing without audit or reconstruction requirements;
- CQRS without meaningfully different read and write needs;
- domain events without an identified consumer;
- repositories for every type regardless of aggregate boundaries;
- generic base entities that erase domain meaning;
- universal status or metadata models shared by unrelated concepts;
- versioning without a defined history or concurrency requirement;
- soft deletion without recovery, audit, or retention requirements.

Use the simplest model that enforces current domain behavior and can evolve
without losing important information.