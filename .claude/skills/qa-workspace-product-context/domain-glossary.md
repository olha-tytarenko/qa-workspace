# Domain Glossary

## User

A person with an account in QA Workspace.

A user may belong to multiple workspaces and may have a different role in each
workspace.

## Workspace membership

The relationship between a user and a workspace.

A workspace membership defines the user's workspace-level role, permissions,
and membership status.

Do not store workspace-specific roles or permissions directly on the user.

## Workspace role

A set of permissions assigned to a workspace membership.

Initial roles may include:

* `owner`: manages the workspace, its members, and workspace-level settings;
* `member`: creates and manages projects, features, requirements, and QA
  artifacts;
* `viewer`: can inspect workspace content without modifying it.

Treat the initial role model as provisional until authorization requirements
are finalized.

Professional functions such as Product Manager, Business Analyst, QA Engineer,
and Software Engineer are user personas, not workspace roles.

## Workspace

The top-level collaboration and authorization boundary containing projects,
memberships, and workspace-level settings.

## Project

A collection of related features and their product and QA artifacts within a
workspace.

A project belongs to exactly one workspace.

## Feature

A bounded product change or capability being specified and verified.

A feature belongs to a project and acts as the primary container for its
requirements, analyses, acceptance criteria, and test cases.

## Product artifact

A structured item used to describe the expected behavior of a feature.

Requirements and acceptance criteria are product artifacts.

## QA artifact

A structured item used to describe how expected behavior will be verified.

Test cases are QA artifacts.

## Requirement

A statement describing required behavior, a business rule, a constraint, or a
quality attribute.

A requirement belongs to a feature.

A requirement is not automatically considered clear, reviewed, testable, or
approved merely because it has been created.

## Requirement analysis

A structured AI-assisted evaluation of one or more requirements for ambiguity,
missing information, contradictions, testability issues, and relevant edge
cases.

A requirement analysis produces findings and may propose clarification
questions.

An analysis does not modify or approve its source requirements.

## Finding

An individual issue or observation produced during requirement analysis.

A finding should identify its source requirement and explain the concern it
detected.

A finding is a proposal for human review, not an established product fact.

## Clarification question

A question intended to resolve missing, ambiguous, or contradictory product
information.

A clarification question should reference the requirement or finding that
caused it to be raised.

An answer to a clarification question does not silently modify a requirement.
Any resulting requirement change must remain explicit.

## Acceptance criterion

A verifiable condition that must hold for a requirement to be considered
correctly implemented.

An acceptance criterion must be derived from and traceable to at least one
requirement.

Acceptance criteria describe observable outcomes rather than implementation
details, unless the implementation itself is part of the requirement.

## Test case

A structured verification scenario used to determine whether expected behavior
has been implemented correctly.

A test case may contain preconditions, test steps, test data, and expected
results.

A test case must be traceable to at least one requirement. It may use
acceptance criteria as input when defining the verification scenario, but
acceptance criteria are not separate coverage targets in the MVP.

## Precondition

A state or condition that must be true before a test case can be executed.

## Test step

An action performed as part of a test case.

A test step may have an expected result describing the observable outcome of
that action.

## Test data

Input values, records, user states, configuration, or other data required to
execute a test case.

## Expected result

The observable outcome that should occur after a test step or test case is
executed.

## Traceability

The ability to follow explicit relationships between a feature, its
requirements, acceptance criteria, and test cases.

Acceptance criteria are derived from requirements. Test cases verify
requirements through explicit coverage links.

Traceability should make it possible to explain:

* which requirement an acceptance criterion was derived from;
* which requirements a test case verifies;
* why a product or QA artifact exists.

## Coverage link

An explicit relationship stating that a test case verifies all or part of a
requirement.

A coverage link may be proposed by AI but must be reviewed by a human before
being treated as confirmed.

A coverage link does not by itself prove that the test case adequately verifies
the requirement.

## Coverage gap

A requirement, behavior, or identified risk for which no adequate test case
has been linked.

A missing coverage link creates a structural coverage gap. An existing link may
still represent insufficient coverage if the linked test case does not
adequately verify the requirement.

Coverage gaps may be detected or proposed by AI, but their significance and
resolution remain subject to human review.

## Review

The process in which a user evaluates an artifact or AI-generated suggestion
and decides whether it should be accepted, changed, or rejected.

Review is distinct from editing. Editing an artifact or suggestion does not
automatically mean that the user has approved it.

## Review decision

An explicit human decision about an artifact or AI-generated suggestion.

A review decision may initially be:

* `accepted`;
* `rejected`;
* `changes_requested`.

Do not infer a review decision solely from a user viewing or editing content.

## Content status

The current lifecycle state of an artifact.

Initial statuses may include:

* `draft`: the artifact is still being prepared;
* `in_review`: the artifact is awaiting a human decision;
* `approved`: a user has explicitly approved the artifact;
* `rejected`: a user has explicitly rejected the artifact.

The exact statuses, transitions, and permissions belong to the domain model and
must not be inferred from this glossary.

## Content provenance

Information describing how an artifact or suggestion originated.

Initial provenance types may include:

* `human_created`;
* `ai_generated`;
* `ai_generated_human_edited`.

Provenance is independent of content status. For example, an AI-generated test
case may later have an `approved` status while retaining its AI-generated
provenance.

## AI-generated suggestion

Content proposed by an AI operation for human consideration.

A suggestion does not become an approved product or QA artifact until a user
makes an explicit review decision.

Editing a suggestion does not automatically approve it.

## Approved artifact

A product or QA artifact with an explicit `approved` status.

Approval reflects a human workflow decision. It does not indicate whether the
artifact was originally created by a human or generated by AI.

## Generation run

A recorded execution of an AI operation.

A generation run should preserve:

* the operation type;
* the relevant input;
* the generated output;
* the execution status;
* the provenance metadata needed to understand how the suggestions were
  produced.

A new generation run must not silently overwrite approved artifacts or
unreviewed user edits.
