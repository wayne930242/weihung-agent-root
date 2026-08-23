---
name: leveraging-tasks
description: Use for any source-changing development work.
---

# Leveraging Tasks

Own source-changing work after the agent enters the target project. A dispatcher
may deliver the request, but the target project's instructions and skills govern
execution.

## 1. Ground

Read the request, project instructions, relevant code, existing `CONTEXT.md`,
ADRs, rules, and related specs. Resolve cheap facts from their source.

Classify artifact depth:

- **Inline:** a self-contained mechanical change with no discovery, behavioral
  choice, public contract change, or handoff risk.
- **Durable:** work that needs discovery, changes observable behavior or a
  contract, spans components, or must survive a session or agent handoff.

For durable work, read [MINI-SDD.md](MINI-SDD.md) fully and create or resume its
artifact folder. Existing related artifacts make the work durable.

For debugging, read [DEBUGGING.md](DEBUGGING.md) now and establish its
pre-specification feedback loop before diagnosing or proposing a fix.

**Complete when:** the target project, artifact depth, and applicable sources are
known.

## 2. Requirements

Reuse requirements already established in the conversation. Resolve factual gaps
with `investigating` or `inspecting`. Resolve decisions belonging to the user with
`grilling`; use `grill-with-docs` when domain terms or an ADR should also persist.

Invoke `domain-modeling` when programming touches domain behavior, terminology,
invariants, or bounded-context boundaries.

Durable work records the outcome, actors, scope, scenarios, decisions, and open
questions in `requirements.md`.

**Complete when:** no open question blocks an observable specification.

## 3. Spec

Inspect the affected code and applicable project standards. Write the observable
contract, edge cases, compatibility constraints, non-goals, applied standards,
and validation strategy. For programming, specify the agent-operated interface
that will prove correctness and any separate human question about
appropriateness. Durable work records this in `spec.md` and links sources rather
than copying them.

Present a durable spec to the user and wait for explicit confirmation. A clear
inline request is already the approved contract for a mechanical change.

**Complete when:** the contract is explicit and, for durable work, confirmed by
the user. Production-source editing starts only after this point.

## 4. Design

Choose the smallest approach that satisfies the approved contract and current
project architecture. Identify affected interfaces, data flow, precedent,
trade-offs, risks, and verification seams. Durable work records these in
`design.md`.

- For debugging, continue the design and implementation steps in
  [DEBUGGING.md](DEBUGGING.md).
- Invoke `codebase-design` when module interfaces, seams, adapters, or
  architectural shape changes.
- Invoke `prototype` when a named design question is best settled by a disposable
  experiment.
- Invoke `tdd` for every programming change. It selects a red-capable test or
  real interface for agent-owned correctness and separates any human final check
  for appropriateness.
- For deployment, apply the project's deployment rules and exact deploy skill.
- Invoke a project skill when its scope exactly matches the work.

Return to an earlier phase when new information changes user intent or observable
behavior. Update only the design when the contract remains unchanged.

**Complete when:** implementation can proceed without inventing product behavior
or architecture while coding.

## 5. Implement

Use the harness-native plan for sequencing and the project's exact skills for
execution. Work in narrow, verifiable slices and keep unrelated cleanup outside
the diff. Continue `tdd` one vertical red-green slice at a time for every
programming change. Carry confirmed domain language into identifiers and tests,
keep invariants in the domain model, and translate external or cross-context
models at adapters. Mini SDD creates no task list, agent state, or implementation
diary.

**Complete when:** every approved behavior is implemented and no extra behavior
was added.

## 6. Verify

Run the planned checks. Agent-owned correctness uses the closest available real
interface: tests, CLI, API, runtime or operational harnesses, Chrome/browser
automation, computer use, or an equivalent project-native surface. Review
separately:

- **Standards:** project conventions and relevant code-quality rules.
- **Spec:** missing, incorrect, or unrequested behavior against the approved
  contract.
- **Domain:** ubiquitous language, invariant placement, bounded contexts, and
  adapter translations remain aligned with the confirmed model.
- **Appropriateness:** when specified, the human judges whether an already
  working result is suitable for its users and context.

Durable work records requirement-to-evidence mapping, deviations, and gaps in
`verification.md`. Keep local verification, commit, push, CI, deployment, and
browser proof as distinct claims.

Keep automated results, interface observations, operational evidence, human
appropriateness verdicts, and gaps distinct. Human review does not replace a
missing correctness result. Documentation-only changes use agent inspection and
applicable static checks.

**Complete when:** every programming item has agent-owned correctness evidence,
every required appropriateness decision has a human verdict, and every remaining
gap is explicitly reported as incomplete.
