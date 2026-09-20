---
name: qa-workspace-ai-generation
description: >
  Design, implement, review, or change QA Workspace AI-generation workflows.
  Use for requirement analysis, ambiguity detection, clarification questions,
  edge cases, acceptance-criteria generation, test-case generation, proposed
  coverage links, prompt construction, structured outputs, model integration,
  generation provenance, regeneration, AI quality evaluation, or prompt
  versioning. Do not use for generic backend queue infrastructure, frontend-only
  presentation, or product behavior unrelated to AI generation.
---

# QA Workspace AI Generation

Build controlled AI-generation pipelines for QA Workspace.

Use AI to propose structured product and QA artifacts. Never treat generated
content as authoritative or approved without an explicit human decision.

Follow the core principle:

```text
AI proposes. Humans decide.
```

Keep generation provider-agnostic unless the repository has explicitly selected
a provider.

## Establish context

Before changing an AI workflow:

1. Apply `qa-workspace-product-context`.
2. Apply `qa-workspace-evolve-domain-model` when changing generated artifact
   types, provenance, lifecycle, or relationships.
3. Apply `qa-workspace-backend-api-patterns` when changing jobs, persistence,
   SSE, authorization, or provider integration.
4. Inspect the existing prompt registry, schemas, generation services,
   provider adapters, evaluation cases, and generation-run model.
5. Identify the exact AI operation being changed.
6. Identify its authoritative inputs and expected structured output.
7. Identify which decisions remain exclusively human.
8. Identify how the result will be evaluated before changing the prompt or
   model.

Do not modify a prompt without understanding its output consumers and current
evaluation coverage.

## Use explicit generation operations

Model each AI capability as a separate operation with its own input contract,
output schema, prompt version, and evaluation criteria.

Initial operations may include:

```text
analyze_requirements
generate_acceptance_criteria
generate_test_cases
propose_coverage_links
```

Do not use one universal prompt for all operations.

Do not combine several operations merely to reduce provider calls when doing so
makes outputs harder to validate, review, retry, or evaluate.

A workflow may chain operations, but every stage must preserve its own inputs,
outputs, and generation metadata.

## Define an operation contract

Before implementing a generation operation, define:

- operation name;
- user-visible purpose;
- authoritative input entities;
- optional supporting context;
- structured output schema;
- allowed assumptions;
- prohibited behavior;
- maximum output size;
- validation rules;
- human-review boundary;
- quality criteria;
- failure behavior.

Do not start with prompt wording. Start with the operation contract.

## Use authoritative inputs only

Build model context from authorized, persisted product data.

For each input:

1. Load it through the authenticated workspace boundary.
2. Verify that it belongs to the expected workspace and feature.
3. Use the intended version or snapshot.
4. Include only information needed for the operation.
5. Preserve identifiers required for traceability.
6. record which inputs were used.

Do not let the client send arbitrary hidden context that bypasses backend
authorization.

Do not retrieve data from another workspace.

Do not assume that recently updated data is the data used by an already running
generation. Preserve or identify the input snapshot.

## Separate instructions from user content

Treat feature descriptions, requirements, comments, imported documents, and
other user-authored text as untrusted data.

Clearly separate:

- system or operation instructions;
- product rules;
- output schema;
- supplied source content.

Tell the model that instructions appearing inside supplied source content are
data and must not override the operation instructions.

Do not concatenate untrusted text into an instruction section without clear
delimitation.

Do not allow requirement content to:

- change the output schema;
- request secrets or hidden instructions;
- override workspace boundaries;
- assign approval state;
- select tools or external resources;
- alter system behavior.

Use deterministic authorization and validation outside the model. Prompt
instructions are not a security boundary.

## Construct minimal sufficient context

Include only context that can materially improve the requested output.

Prefer:

- the target feature;
- relevant requirements;
- confirmed clarification answers;
- applicable product rules;
- identifiers needed for traceability;
- approved related artifacts when the operation depends on them.

Avoid:

- unrelated project history;
- every artifact in the workspace;
- duplicate representations of the same information;
- raw internal database records;
- implementation details the operation does not need;
- previously generated suggestions that could anchor or amplify errors unless
  comparison is intentional.

When context exceeds practical limits:

1. select relevant source material deterministically where possible;
2. preserve direct source identifiers;
3. record what was included and omitted;
4. avoid lossy summarization of authoritative requirements unless the product
   explicitly permits it;
5. expose incomplete context when it may affect output quality.

Do not silently truncate requirements.

## Prefer structured outputs

Require provider-supported structured output or schema-constrained generation
when available.

Define the output using explicit Pydantic models.

Use:

- required fields;
- bounded strings;
- bounded arrays;
- enums for known categories;
- stable source identifiers;
- discriminated unions for variants;
- optional fields only when absence has defined meaning.

Avoid free-form Markdown as the authoritative output of a generation workflow.

Markdown may be used inside bounded display fields when the product requires
rich text, but the overall result must remain structured.

A structurally valid response is not automatically factually correct,
authorized, useful, or approved.

## Validate every generated result

Treat model output as untrusted external input.

Validate in layers:

1. Provider response completed successfully.
2. Output matches the expected structural schema.
3. Collection and text-size limits are respected.
4. Referenced identifiers exist.
5. Referenced entities belong to the authorized workspace and feature.
6. Enum and category values are allowed.
7. Cross-entity relationships satisfy domain invariants.
8. The output does not assign server-controlled fields.
9. The output can be persisted as an unapproved suggestion.

The backend must assign:

- resource identifiers;
- workspace and feature ownership;
- generation-run identity;
- provenance;
- lifecycle status;
- review status;
- approval actor and timestamp.

Do not trust identifiers, ownership, approval state, or permissions generated by
the model.

## Preserve source grounding

Every generated finding, acceptance criterion, test case, or coverage proposal
must reference the requirement or requirements that support it.

Reject or flag generated items with missing, inaccessible, or invalid source
references.

Do not let the model cite a requirement only by copied text when a stable
identifier is available.

A source reference indicates where the suggestion came from. It does not prove
that the suggestion is correct.

When a suggestion contains an inference not explicitly supported by its source,
represent it as an assumption or clarification need rather than a confirmed
fact.

## Analyze requirements without inventing behavior

The `analyze_requirements` operation should identify possible:

- ambiguities;
- missing information;
- contradictions;
- testability problems;
- unstated dependencies;
- boundary conditions;
- relevant edge cases.

Each finding should contain:

- source requirement identifiers;
- category;
- concise explanation;
- why the issue matters;
- a proposed clarification question when appropriate.

Do not rewrite or modify the source requirement automatically.

Do not invent business behavior to close a gap.

Do not present a possible issue as a confirmed defect in the requirement.

Avoid generating generic findings that could apply to almost any feature.

Prefer fewer specific findings over a long list of low-value possibilities.

## Generate useful clarification questions

Generate a clarification question only when its answer could materially affect:

- user-visible behavior;
- validation;
- permissions;
- data ownership;
- state transitions;
- failure handling;
- acceptance criteria;
- test cases.

A clarification question should:

- reference its source requirement or finding;
- ask one decision at a time;
- be answerable by a product stakeholder;
- explain why the answer matters when that is not obvious;
- avoid embedding an unsupported preferred answer.

Do not ask questions already answered by the supplied context.

Do not generate questions about implementation details unless the
implementation itself is a product requirement.

## Generate acceptance criteria from requirements

The `generate_acceptance_criteria` operation must use reviewed requirements as
its authoritative source.

Each generated acceptance criterion should:

- reference at least one source requirement;
- describe observable behavior;
- define a verifiable outcome;
- avoid unnecessary implementation details;
- use terminology from the domain glossary;
- preserve stated constraints and permissions;
- expose unresolved information instead of inventing it.

Do not generate an acceptance criterion that introduces new product behavior
without marking it as an assumption or clarification need.

Avoid duplicating the source requirement without making it more verifiable.

Do not assume that generated acceptance criteria are approved.

## Generate structured test cases

The `generate_test_cases` operation must use requirements and their acceptance
criteria as inputs.

Each generated test case should contain the relevant:

- title;
- source requirement identifiers;
- purpose or scenario;
- preconditions;
- test data;
- ordered test steps;
- expected results;
- classification or priority when supported by evidence.

Each test case must link directly to at least one requirement.

Acceptance criteria may guide test-case generation but are not separate coverage
targets in the MVP.

Generate tests for relevant:

- primary paths;
- validation failures;
- permission boundaries;
- state transitions;
- error behavior;
- boundary values;
- identified edge cases.

Do not generate meaningless combinations solely to increase test count.

Do not invent unavailable test data, system behavior, roles, or integrations as
facts.

Represent missing information explicitly.

## Propose coverage links conservatively

The `propose_coverage_links` operation may suggest relationships between test
cases and requirements.

Each proposal must reference:

- an existing requirement;
- an existing test case;
- a concise explanation of the behavior covered.

The model may propose a link but must not confirm or approve it.

Validate that both resources belong to the same feature and workspace.

The coverage dashboard must use confirmed persisted relationships, not model
confidence or semantic similarity alone.

Do not treat a proposed link as proof that the test case adequately covers the
requirement.

Do not create acceptance-criterion coverage links in the MVP.

## Represent uncertainty explicitly

Do not ask the model for false certainty.

When supported by the operation schema, distinguish:

- directly supported conclusions;
- reasonable inferences;
- unresolved questions;
- unsupported suggestions.

Use model confidence only as supplemental metadata. Do not treat it as a
calibrated probability unless calibration has been demonstrated.

Do not automatically accept or hide content based solely on a model-generated
confidence score.

Prefer an explicit explanation of missing evidence over an arbitrary percentage.

## Keep human review authoritative

Persist generated output as suggestions awaiting human review.

Users must be able to:

- inspect a suggestion;
- inspect its source requirements;
- edit it;
- accept it;
- reject it;
- understand whether it was generated or human-created.

Editing does not automatically imply approval.

Acceptance and approval must be explicit product actions.

Do not merge generated output directly into approved artifacts without a human
decision.

Do not design the interface or backend so that rejection is substantially more
difficult than acceptance.

## Preserve provenance

For each generation run, preserve the relevant:

- operation type;
- provider;
- provider model identifier;
- prompt version;
- output-schema version;
- model parameters that affect behavior;
- source entity identifiers;
- source versions or input snapshot;
- generation timestamp;
- execution status;
- retry or attempt metadata;
- token usage when available;
- cost metadata when available and reliable;
- generated output or a durable reference to it;
- validation outcome;
- failure category.

Do not rely on a mutable model alias when the provider exposes a more specific
model version or snapshot.

Do not store or expose hidden chain-of-thought.

Store concise user-facing explanations or evidence references only when the
product needs them.

## Version prompts deliberately

Assign a stable version to every production prompt or prompt configuration.

Increment the version when changing behaviorally relevant:

- instructions;
- examples;
- output schema;
- context construction;
- model;
- tool configuration;
- decoding or reasoning parameters.

A formatting-only code change does not necessarily require a prompt version
change.

Keep prompt templates reviewable in source control or an equivalently auditable
prompt registry.

Do not edit production prompts exclusively through an untracked provider
dashboard.

Tie evaluation results to the exact prompt, schema, and model configuration.

## Keep provider code behind an adapter

Expose a provider-independent generation interface to application code.

The adapter should translate:

- internal operation input;
- model and prompt configuration;
- structured-output schema;
- timeout and cancellation;
- provider response;
- usage metadata;
- provider errors.

Do not leak provider-specific response objects into domain or API models.

Do not create an elaborate multi-provider abstraction before a second provider
or a concrete portability requirement exists.

Keep the initial adapter narrow enough that a provider change does not require
rewriting product logic.

## Select models by measured requirements

Choose a model according to:

- quality on the operation's evaluation set;
- structured-output reliability;
- latency;
- cost;
- context requirements;
- availability and rate limits;
- privacy and data-handling requirements.

Do not choose a model only because it is newest, largest, or cheapest.

Use a smaller model when it meets the measured quality threshold.

Use a stronger model when the quality difference materially affects the product
outcome.

Run evaluations before changing a production model or model version.

## Configure generation intentionally

Set generation parameters per operation when the provider supports them.

Prefer stable, reproducible behavior for structured product and QA artifacts.

Do not assume that setting temperature to zero makes output deterministic.

Bound:

- maximum output tokens;
- number of generated items;
- input size;
- execution time;
- retry count.

Do not request verbose explanations when structured evidence and concise
reasoning are sufficient.

Do not expose provider parameters directly to ordinary end users without a
clear product requirement.

## Handle refusals and incomplete outputs

Treat provider refusal, truncation, schema failure, timeout, rate limiting, and
content filtering as distinct outcomes.

Do not persist a partial or malformed result as a successful generation.

When output is incomplete:

1. mark the attempt with a structured failure category;
2. preserve safe diagnostic metadata;
3. decide whether a technical retry is allowed;
4. communicate the failure without exposing provider internals;
5. leave existing suggestions and approved artifacts unchanged.

Do not hide a refusal by generating fabricated fallback content.

## Retry technical failures carefully

Retry only failures likely to be transient, such as:

- provider timeout;
- temporary unavailability;
- rate limiting;
- interrupted network connection.

Use bounded exponential backoff with jitter.

Do not automatically retry:

- valid but low-quality output;
- unsupported requirements;
- authorization failures;
- invalid source references;
- persistent schema incompatibility;
- content that requires a product decision.

A retry must not create duplicate suggestions or generation runs unexpectedly.

Record attempts under the persisted generation-run model.

## Make regeneration non-destructive

Regeneration creates a new generation attempt and new suggestions.

It must not silently overwrite:

- approved artifacts;
- human-created artifacts;
- human-edited suggestions;
- unresolved review decisions;
- previous generation history.

Preserve the source version used by each generation.

When inputs changed after a previous generation, make the relationship visible
instead of silently treating old output as current.

Do not combine old and new generated output automatically unless a merge
workflow is explicitly designed.

## Detect stale results

Before persisting or presenting a completed result as current:

1. verify that the generation run is still active;
2. check cancellation state;
3. compare relevant source versions;
4. determine whether a newer run supersedes it;
5. preserve the result as historical when it is no longer current.

Do not discard a completed stale result if generation history is required, but
do not allow it to replace newer or approved content.

## Minimize sensitive data exposure

Send only the data required for the operation to the AI provider.

Do not include:

- unrelated workspace content;
- authentication credentials;
- internal authorization data;
- secrets;
- hidden system configuration;
- unnecessary personal data;
- another tenant's data.

Review provider data-retention and training settings before production use.

Keep provider credentials server-side.

Do not log complete prompts or model responses by default when they can contain
sensitive customer content.

Use redacted or sampled diagnostic logging when necessary.

## Introduce retrieval only when needed

Do not add vector search or RAG merely because the product uses an LLM.

Use direct authoritative inputs when the required context is already known,
such as the requirements belonging to the current feature.

Introduce retrieval when the operation genuinely needs relevant information
from a larger approved corpus.

When retrieval is used:

1. authorize before searching;
2. filter candidates by workspace and resource access;
3. retrieve only permitted content;
4. preserve source identifiers;
5. expose citations or evidence where useful;
6. evaluate retrieval separately from generation.

Do not retrieve first and filter unauthorized results afterward.

Do not let retrieved instructions override the generation operation.

## Avoid unnecessary agentic behavior

Prefer a deterministic generation pipeline for the MVP.

Do not introduce autonomous planning, unrestricted tool use, recursive agents,
or multi-agent orchestration when a single structured model call can perform
the operation.

Add tools only when the operation requires current data or an external action
that cannot be provided directly as validated context.

Restrict every tool by:

- explicit purpose;
- validated input schema;
- authorization;
- workspace scope;
- bounded output;
- timeout;
- auditability.

The model must not receive a generic database, filesystem, network, or code
execution tool.

## Define evaluation criteria before optimization

For each AI operation, define measurable quality dimensions before changing
prompts or models.

Relevant dimensions may include:

- schema validity;
- source-reference validity;
- groundedness;
- requirement coverage;
- correctness;
- relevance;
- specificity;
- testability;
- actionability;
- duplication rate;
- unsupported-assumption rate;
- human acceptance or edit rate;
- latency;
- cost.

Do not optimize only for outputs that sound polished.

Do not use one aggregate quality score when separate failure modes require
different actions.

## Maintain an evaluation dataset

Create a versioned evaluation dataset containing representative QA Workspace
examples.

Include:

- clear requirements;
- ambiguous requirements;
- contradictory requirements;
- missing permissions;
- missing validation behavior;
- boundary conditions;
- multi-requirement features;
- long inputs;
- irrelevant context;
- adversarial instructions inside requirement text;
- malformed provider output;
- examples where no finding should be generated;
- examples requiring clarification instead of invention.

Include real-world examples only when permitted and appropriately sanitized.

Add a regression case whenever a production or development failure reveals a
new repeatable failure mode.

Do not build the dataset only from ideal examples used while writing the prompt.

## Use layered evaluation

Evaluate deterministic properties with code:

- schema validity;
- identifier validity;
- ownership;
- allowed categories;
- item-count limits;
- duplicate identifiers;
- required traceability;
- forbidden approval state.

Evaluate semantic quality with:

- explicit rubrics;
- human review;
- calibrated model-based graders where appropriate.

Do not ask a model-based grader only whether an output is “good.”

Give graders operation-specific criteria and evidence.

Periodically compare model-based grades with human judgments.

Do not use the same prompt and assumptions for both generation and grading when
that would reproduce the same blind spots.

## Compare prompt and model changes

Before adopting a prompt, schema, or model change:

1. run the current and proposed configurations on the same evaluation dataset;
2. compare each quality dimension;
3. inspect regressions, not only averages;
4. compare latency and cost;
5. review representative failures;
6. record the evaluated configuration;
7. require human review for material behavior changes.

Do not promote a change solely because several hand-picked examples improved.

Set operation-specific acceptance thresholds.

Block promotion when critical invariants fail even if the average score
improves.

## Keep CI deterministic

In ordinary CI:

- mock external model calls;
- test context construction;
- test prompt selection and versioning;
- test provider request mapping;
- test schema validation;
- test invalid references;
- test persistence and provenance;
- test retry and failure classification;
- test regeneration safety;
- test authorization boundaries.

Do not make every pull request depend on a live model call.

Run live-model evaluations separately when prompts, models, schemas, or context
construction change.

Record the exact configuration used in live evaluations.

Do not treat one successful live response as a regression test.

## Observe production quality

Track operational metrics such as:

- generation success and failure rate;
- schema-validation failure rate;
- provider refusal rate;
- latency;
- token usage;
- estimated cost;
- retry rate;
- cancellation rate.

Track product-quality signals such as:

- suggestion acceptance rate;
- rejection rate;
- human edit rate;
- regeneration rate;
- invalid-reference rate;
- duplicate suggestion rate;
- clarification-question resolution rate.

Interpret behavioral metrics carefully. A high acceptance rate does not prove
correctness, and a high edit rate does not necessarily mean failure.

Do not optimize metrics by making acceptance easier than rejection.

## Review AI-generation changes

Before completing an AI-generation change, verify:

- the operation has a clear contract;
- authoritative inputs are authorized and versioned;
- untrusted content is separated from instructions;
- the output uses an explicit schema;
- identifiers and ownership are validated;
- generated items remain unapproved suggestions;
- every item preserves source traceability;
- uncertainty is exposed rather than invented;
- prompt, schema, and model versions are recorded;
- regeneration preserves approved and human-edited content;
- stale results cannot replace current content;
- technical retries cannot duplicate effects;
- sensitive content is not exposed unnecessarily;
- evaluation cases cover the changed behavior;
- deterministic tests pass;
- live evaluation was run when the behavioral configuration changed.

Do not claim that an AI workflow is reliable based only on schema validity or a
small number of manually inspected examples.