---
name: leveraging-tasks
description: Use for source-changing development; keep low-reuse local work inline and persist only durable decisions.
---

# Leveraging Tasks

Own source-changing work after entering the target project. A dispatcher may
deliver the request; the target project's instructions and skills govern
execution. Phases run Ground → Requirements → Spec → Design → Implement →
Verify. Return to an earlier phase whenever new information changes user intent
or observable behavior; update only the design when the contract holds.

## Ground

Declare the change **Inline** or **Durable** before the first production edit:

- **Inline:** requirements are clear, impact is localized, implementation and
  verification fit this run, and the decisions have little future reuse. Inline
  work may change observable behavior and writes no artifact files.
- **Durable:** a decision, constraint, or proof must outlive this run —
  unconfirmed design, a public or external contract, a migration,
  cross-component coordination, continuity across a session or handoff, a
  user-requested spec, or an active related artifact.

Escalate to durable instead when the request carries material ambiguity, spans
modules or sessions, sets a contract meant to last, is high risk, expands scope
beyond what was asked, or when the user wants to see the spec first.

Inline work opens its reply with these two lines, then executes. They are
required output, not preamble, and no brevity rule removes them:

    Inline — Contract: <one sentence of the observable behavior after the change>
    Authorization: <the user's explicit source-change request>

Approval already given is not requested again.

Durable work reads [MINI-SDD.md](MINI-SDD.md) and creates or resumes its folder
before it specifies anything; that folder is its declaration.
Debugging reads [DEBUGGING.md](DEBUGGING.md) and establishes its red-capable
loop before diagnosing.

## Requirements

Resolve facts from their source; use `investigating` or `inspecting` when the
search is wide. Send decisions that belong to the user to `grilling`, or
`grill-with-docs` when domain terms or an ADR should persist. Invoke
`domain-modeling` when terminology, invariants, or context boundaries move.

**Complete when:** no open question blocks an observable specification.

## Spec

State the observable contract, edge cases, compatibility constraints, non-goals,
and the applied project standards. Name the agent-operated interface that will
prove correctness, and any separate human question about appropriateness.
Write the durable contract to `spec.md` under `Status: proposed` before
presenting it — a spec that exists only in the reply is not a durable spec —
then wait for explicit user confirmation. `proposed` forbids production-source
editing; artifacts, sandboxes, and read-only work stay open. Only the user's
explicit approving reply sets `Status: approved`, `Approved at`, and
`Approved from` — never elapsed time, a silent user, or the agent's own
judgment. An inline `Contract:` is already approved under its recorded
`Authorization:`.

## Design

Choose the smallest approach that fits the confirmed contract and the project's
existing architecture. Invoke `codebase-design` when interfaces, seams, or
adapters change, `prototype` when a named question is cheaper to settle by
throwaway experiment, `tdd` for every programming change, and the project's
exact skill when its scope matches. Design is done when implementation invents
no product behavior or architecture.

## Implement

The harness-native plan owns sequencing. Work one red-green slice at a time
through `tdd`. Mini SDD creates no `tasks.md`, agent state, or diary.

## Verify

Correctness is agent-owned: exercise the closest available real interface —
tests, CLI, API, runtime or operational harness, browser automation, computer
use, or another project-native surface. Documentation-only changes use agent
inspection and static checks. Then review the diff separately against project
standards, the approved contract, and the confirmed domain model. A human
verdict covers appropriateness only: whether an already-working result suits its
users and context. It never substitutes for missing correctness evidence.

Give every requirement in the contract its own `Requirement | Evidence | Result`
row, where `Result` is `pass`, `fail`, or `unknown` and `Evidence` names the real
interface exercised and what it observed. A green suite, a passing unrelated
check, or an agent's claim of completion is not evidence for a requirement
nothing exercised; that requirement stays `unknown`.

**Complete when:** every programming item has agent-owned correctness evidence,
every required appropriateness decision has a human verdict, and every remaining
gap is reported as incomplete. Keep local verification, commit, push, CI,
deployment, and browser proof as distinct claims.
