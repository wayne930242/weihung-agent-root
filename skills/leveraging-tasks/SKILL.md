---
name: leveraging-tasks
description: Use for source-changing development; keep low-reuse local work inline and persist only durable decisions.
---

# Leveraging Tasks

Own source-changing work after entering the target project; its instructions and
skills govern execution. Phases run Ground → Requirements → Spec → Design →
Implement → Verify. Return when user intent or observable behavior changes.

Open every run with one working interpretation in the model's own words:

    Alignment: <the requested task and intended outcome>

Proceed when decision-complete; route a consequential user-owned decision to `grilling`.

## Ground

Declare the change **Inline** or **Durable** before the first production edit:

- **Inline:** requirements are clear, impact is localized, implementation and
  verification fit this run, and the decisions have little future reuse. Inline
  work may change observable behavior and writes no artifact files.
- **Durable:** a decision, constraint, or proof must outlive this run —
  unconfirmed design, a public or external contract, a migration,
  cross-component coordination, continuity across a session or handoff, a
  user-requested spec, or an active related artifact.

Escalate to durable when the request carries material ambiguity, spans modules
or sessions, sets a lasting contract, is high risk, expands scope, or requests a spec first.

Inline work follows Alignment with these two lines. They are required output:

    Inline — Contract: <one sentence of the observable behavior after the change>
    Authorization: <the user's explicit source-change request>

Approval already given is not requested again.

Before the first production edit, state:

    Reality anchor: <the simplest credible contact with reality and its checkpoint>

Choose it from the task, user, and target project. The method inside may use an
executable check, user operation, human judgment, or focused review.

Durable work reads [MINI-SDD.md](MINI-SDD.md) and creates or resumes its folder
before it specifies anything; that folder is its declaration.
Debugging reads [DEBUGGING.md](DEBUGGING.md) and establishes its red-capable
loop before diagnosing.

## Requirements

Resolve facts from their source; use `investigating` or `inspecting` when search
is wide. Send user decisions to `grilling`, or `grill-with-docs` when domain
terms or an ADR should persist. Invoke
`domain-modeling` when terminology, invariants, or context boundaries move.

**Complete when:** no open question blocks an observable specification.

## Spec

State the observable contract, edge cases, compatibility constraints, non-goals,
and the applied project standards. Name the reality anchor and checkpoint.
Persist the durable contract in `spec.md` under `Status: proposed` before presenting
it, then await explicit user confirmation.
`proposed` keeps production source untouched while artifacts and read-only work
stay open. Only the user's approving reply sets `Status: approved`, `Approved at`,
and `Approved from`. An inline `Contract:` is approved by its `Authorization:`.

## Design

Choose the smallest approach that fits the confirmed contract and architecture.
Invoke `codebase-design` when interfaces or seams change, `prototype` when a
named question is cheaper to settle by experiment, and the project's exact skill.
Design is done when implementation invents no product behavior or architecture.

## Implement

The harness-native plan owns sequencing. Follow the target project's native
practices and work in the smallest useful increments. Mini SDD creates no
`tasks.md`, agent state, or diary.

## Verify

Exercise the chosen reality anchor and capture what it observed. Then review the
diff separately against project standards, the approved contract, and the
confirmed domain model. A human checkpoint owns criteria that require human
judgment; record its verdict distinctly from executable or review evidence.

Give every requirement in the contract its own `Requirement | Evidence | Result`
row, where `Result` is `pass`, `fail`, or `unknown` and `Evidence` names the real
interface exercised and what it observed. A green suite, a passing unrelated
check, or an agent's claim of completion is not evidence for a requirement
nothing exercised; that requirement stays `unknown`.

**Complete when:** every requirement has credible evidence from its chosen
anchor and every remaining gap is reported as incomplete. Keep local
verification, commit, push, CI, deployment, and browser proof as distinct claims.
