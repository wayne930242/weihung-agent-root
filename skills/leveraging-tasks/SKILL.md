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

Classify artifact depth before specifying:

- **Inline:** requirements are clear, impact is localized, implementation and
  verification fit this run, and the decisions have little future reuse. Inline
  work may change observable behavior and writes no artifact files.
- **Durable:** a decision, constraint, or proof must outlive this run —
  unconfirmed design, a public or external contract, a migration,
  cross-component coordination, continuity across a session or handoff, a
  user-requested spec, or an active related artifact.

Durable work reads [MINI-SDD.md](MINI-SDD.md) and creates or resumes its folder.
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
Present a durable spec and wait for explicit user confirmation.
Production-source editing starts only after this point. A clear inline request
is already its own approved contract.

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

**Complete when:** every programming item has agent-owned correctness evidence,
every required appropriateness decision has a human verdict, and every remaining
gap is reported as incomplete. Keep local verification, commit, push, CI,
deployment, and browser proof as distinct claims.
