# Integrated Mini SDD specification

Status: confirmed by user on 2026-08-23

## Behavioral contract

### Development routing

- Given a request that changes project source or behavior, when the agent enters
  the target project, then `leveraging-tasks` coordinates the development
  lifecycle using existing specialized skills.
- Given a task dispatched by Straw Boss, when the dispatched agent starts work,
  then it follows the target project's lifecycle; Straw Boss does not create,
  parse, approve, or track SDD artifacts.
- Given a purely read-only question, investigation, or inspection, when no
  implementation is requested, then its specialized skill runs directly and
  does not manufacture implementation artifacts.

### Requirements

- Given an unresolved product or design decision, when facts alone cannot settle
  it, then `grilling` asks the user and records the confirmed outcome, scenarios,
  scope, non-goals, decisions, and remaining questions in `requirements.md`.
- Given a fact discoverable from code, documentation, runtime evidence, or a
  primary source, then the agent resolves it rather than asking the user.
- The requirements phase is complete only when no open question blocks an
  observable specification.

### Specification

- Given settled requirements, when the agent prepares `spec.md`, then
  `investigating` and `inspecting` supply relevant codebase facts, project
  standards, precedents, constraints, and cited evidence.
- `spec.md` states observable behavior, edge cases, compatibility constraints,
  non-goals, applicable standards with their impact, and planned proof. It links
  to sources instead of copying them.
- The agent presents `spec.md` to the user and waits for explicit confirmation.
  Production-source implementation cannot begin while its status is pending.

### Design

- Given a user-confirmed specification, when implementation needs technical
  shaping, then the design phase creates `design.md` with the chosen approach,
  affected interfaces and data flow, relevant precedent, trade-offs, risks, and
  verification seams.
- The design follows current project architecture and documented standards. A
  new ADR is created only for a hard-to-reverse, surprising decision reached
  through a real trade-off.
- `design.md` is the implementation-ready handoff. It does not duplicate the
  behavioral contract or become an operational task tracker.

### Specialized engineering disciplines

- When a change creates or reshapes a module interface or test seam,
  `codebase-design` evaluates depth, interface burden, locality, adapters, and
  testability before implementation.
- When domain language changes or conflicts with code, `domain-modeling`
  challenges the terminology with concrete scenarios and updates the glossary
  or a qualifying ADR at the point the decision is confirmed.
- During implementation, the same domain model governs identifiers, invariants,
  module placement, adapter translations, and test vocabulary. A contradiction
  returns to Requirements or Design instead of being resolved silently in code.
- When a design question is cheaper to answer by experiment than discussion,
  `prototype` creates a clearly marked throwaway artifact, records the question
  and verdict, then keeps only the validated decision in the production design.
- Every programming change uses `tdd`, working one vertical red-green slice at a
  time through the closest credible public or user-facing seam.

### TDD correctness and human appropriateness

- Every programming change invokes `tdd`. Observable behavior changes use a
  red-green vertical slice at a stable public seam; behavior-preserving refactors
  establish or confirm characterization coverage before editing.
- Correctness remains agent-owned. The red-green loop may use deterministic
  tests, CLI, API, runtime or operational harnesses, Chrome/browser automation,
  computer use, or another project-native interface. Browser-facing behavior
  prioritizes the available Chrome or browser path when it is the closest real
  interface.
- Human final check owns appropriateness only: whether an objectively working
  result is suitable for its users or context. It never substitutes for missing
  correctness evidence.
- A confirmed human checkpoint specifies the scenario and environment, reviewer,
  agent-captured correctness evidence, suitability question, pass/revise result,
  and how the verdict returns to implementation.
- One final check is the default. An iterative human-in-the-loop is used only
  when the user chooses repeated feedback to shape the experience during
  Requirements or Design.
- Documentation-only changes use agent review and applicable static checks, not
  a human final check by default.
- A programming criterion closes only with agent-owned correctness evidence. A
  pending human checkpoint leaves the separate appropriateness criterion open.

### Implementation and verification

- Given an implementation-ready design, when execution starts, then the current
  harness's native plan and exact project skills own task sequencing and code
  changes. Mini SDD creates no `tasks.md` and Straw Boss owns no implementation
  detail.
- If implementation discovers information that changes user intent or the
  observable contract, work stops and returns to the relevant earlier phase.
  Purely technical detail that remains within the approved contract may update
  `design.md` without re-interviewing the user.
- Before completion, `verification.md` maps every specified behavior to
  agent-operated correctness evidence and any separate human appropriateness
  verdict, records deviations and unresolved gaps, and distinguishes local
  verification from commit, push, CI, deployment, and browser proof.
- Given a diff, branch, or pull-request review, `inspecting` resolves a fixed
  comparison point, identifies the governing spec and standards, and reports
  independent Standards and Spec verdicts without allowing one to mask the
  other.

## Standards applied

- Keep user-invoked orchestration thin and reusable disciplines independently
  reachable; do not create a second workflow owner.
- Use progressive disclosure: the active phase points to its artifact contract,
  and branch-specific reference stays outside the always-loaded root prompt.
- Give every phase a checkable completion criterion.
- Keep one source of truth per decision and treat code/configuration as the
  source for facts that are cheap to rediscover.
- Preserve human control at product and architecture decisions while delegating
  factual discovery and mechanical execution to the agent.
- Keep every skill description to one short trigger sentence; descriptions do
  not summarize the workflow body.
- Remove `grill-with-web` and `open-gui`; no browser GUI workflow remains
  installed or routed.

## Explicit non-goals

- Reproducing Matt Pocock's issue-tracker setup, ticket state machine, or forced
  commit behavior.
- Reproducing Agent OS's command framework or its multi-file shaping layout.
- Moving SDD parsing or artifact thresholds into Straw Boss.
- Creating implementation diaries, duplicate standards files, or durable native
  task lists.

## Confirmation

- User confirmation: confirmed on 2026-08-23
- Persistence threshold: revised on 2026-08-23 so future reuse and coordination,
  not observable behavior alone, determine artifact persistence
- Browser GUI removal: explicitly confirmed by the user on 2026-08-23
- Capability additions and the correctness/appropriateness boundary: explicitly
  confirmed by the user on 2026-08-23
