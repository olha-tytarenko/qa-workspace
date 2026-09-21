---
name: qa-workspace-product-context
description: >
  Apply QA Workspace product rules and terminology when analyzing or changing
  product behavior, workflows, domain concepts, AI-assisted interactions,
  review and approval behavior, requirement traceability, or coverage.
  Use when a task requires product judgment or could affect established product
  invariants. Do not use for purely technical refactoring, styling, dependency
  updates, or implementation work that does not change product behavior.
---

# QA Workspace Product Context

Use the documented product context to keep product decisions consistent with
the purpose, terminology, scope, and principles of QA Workspace.

## Load product context

Before making a product-level decision:

1. Read [product.md](product.md).
2. Read [domain-glossary.md](domain-glossary.md) when the task introduces,
   interprets, or changes domain concepts.
3. Treat the documented context as authoritative unless the user explicitly
   changes it.
4. If the files conflict, surface the conflict instead of choosing silently.

Do not load the glossary for tasks that do not involve domain terminology.

## Evaluate a product change

For each proposed product change:

1. Identify the affected user and their concrete problem.
2. Identify the expected user outcome.
3. Locate the change within the canonical QA Workspace workflow.
4. Identify the applicable product invariants.
5. Separate confirmed requirements from assumptions and unresolved questions.
6. Propose the smallest coherent change that produces the desired outcome.
7. Preserve human control over AI-generated suggestions.
8. Surface only unresolved questions that could materially change the solution.

Begin with the user problem, not with a preferred technology or AI capability.

## Preserve product invariants

Preserve these rules unless the user explicitly changes them:

- AI proposes; humans decide.
- AI-generated suggestions are never silently treated as approved artifacts.
- Users can inspect, edit, accept, or reject AI-generated suggestions.
- Editing a suggestion does not automatically approve it.
- Regeneration does not overwrite approved artifacts or unreviewed user edits.
- Requirements are the primary source for acceptance criteria and test cases.
- Test cases remain traceable to the requirements they verify.
- Missing or ambiguous information is exposed rather than invented.
- Coverage is based on explicit traceability, not an unsupported AI estimate.
- Important product state changes remain explainable and auditable.
- The MVP prioritizes requirement quality and reviewability over maximum
  automation.

Treat these as product constraints, not implementation suggestions.

## Follow the canonical workflow

Place relevant product behavior within this workflow:

1. Create a feature.
2. Add requirements manually. Importing requirements is not part of the MVP.
3. Analyze requirements for ambiguity, omissions, contradictions, testability,
   and edge cases.
4. Present findings and clarification questions for human review.
5. Update or confirm requirements based on explicit human input.
6. Generate acceptance criteria from the reviewed requirements.
7. Generate structured test cases from requirements and acceptance criteria.
8. Let users review, edit, accept, or reject generated suggestions.
9. Link test cases to the requirements they verify.
10. Display traceability and coverage status.
11. Preserve the provenance and review state of resulting artifacts.

Do not introduce a parallel workflow unless the existing workflow cannot
support the use case. Explain why before proposing one.

## Handle uncertainty

Classify relevant information as:

- `known`: explicitly documented or provided by the user;
- `inferred`: strongly implied but not explicitly confirmed;
- `unknown`: missing information that could materially affect behavior;
- `out_of_scope`: intentionally excluded from the current task or product scope.

Never present inferred or unknown information as established fact.

If uncertainty does not affect permissions, data integrity, workflow semantics,
approval behavior, or an irreversible architectural decision:

1. State the assumption when it is relevant to the user.
2. Choose the simplest reversible option.
3. Continue within the established product boundaries.

If uncertainty materially affects any of those areas:

1. Do not implement the affected behavior.
2. Explain the competing interpretations.
3. Ask for a product decision.

Continue with unaffected parts of the task when possible.

## Control scope

Prefer the smallest end-to-end change that provides user value.

Treat work as outside the current task when it:

- solves a different user problem;
- adds an unrequested role or workflow;
- introduces speculative extensibility;
- changes an established product invariant;
- replaces human approval with autonomous AI action;
- requires unrelated domain or architecture changes.

Do not implement out-of-scope work silently. Mention it as possible follow-up
work only when it is relevant.

## Communicate product analysis

When the user asks for product analysis, a feature proposal, or clarification
of requirements, include only the relevant sections from:

- user problem;
- desired outcome;
- applicable product context;
- proposed scope;
- confirmed requirements;
- assumptions;
- open questions;
- acceptance boundary;
- out of scope.

Do not force this structure onto implementation updates or ordinary answers.

## Avoid unsupported product decisions

Do not:

- invent requirements to make a task appear complete;
- treat AI-generated text as authoritative;
- infer approval from viewing or editing content;
- add functionality solely because it is technically convenient;
- apply generic SaaS conventions when QA Workspace defines a specific rule;
- introduce a second term for an existing domain concept;
- change established terminology without explicit confirmation;
- hide ambiguity behind vague implementation language;
- produce a detailed implementation plan before understanding the desired
  user outcome.