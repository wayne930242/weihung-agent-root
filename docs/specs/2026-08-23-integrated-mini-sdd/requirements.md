# Integrated Mini SDD requirements

Created: 2026-08-23

## Outcome

Claude Code and Codex use one lightweight, traceable development flow without
adding another framework beside the existing skills. OpenSpec is no longer an
active route. Straw Boss remains a dispatcher; the dispatched agent consumes
the target project's development flow after entering that project.

## Required flow

1. Exploration and `grilling` clarify the user's outcome, scenarios, scope,
   non-goals, and decisions. Durable work records these in `requirements.md`.
2. `investigating` and `inspecting` gather codebase facts, applicable project
   standards, precedent, and external primary-source evidence. Their findings
   are inputs to `spec.md`, not a second planning system.
3. The agent writes an observable specification and asks the user to confirm it.
   Source implementation does not begin while confirmation is pending.
4. After confirmation, the design phase turns the approved spec into an
   implementation-ready `design.md` using the project's native architecture,
   interfaces, seams, and verification approach.
5. The existing implementation route executes the design. Native model plans
   may sequence work; Mini SDD does not create a parallel `tasks.md` or status
   engine.
6. Verification records requirement-to-evidence traceability and keeps commit,
   push, CI, deployment, and browser proof as distinct states.

## Engineering capability requirements

- Add reusable disciplines for test-driven development, deep-module design,
  active domain modeling, and throwaway prototypes. They are specialized skills
  consumed by the existing lifecycle, not new workflow owners.
- A diff or branch review pins its comparison point and reports Standards and
  Spec as separate verdicts.
- Every programming change enters TDD. A behavior change starts with a
  red-capable check through the selected interface; a behavior-preserving
  refactor first establishes characterization coverage and keeps it green.
- Correctness is agent-owned. For each programming criterion, the agent exercises
  the closest credible interface itself: tests, CLI, API, runtime or operational
  harnesses, Chrome/browser automation, computer use, or another project-native
  surface. Browser-facing behavior prioritizes the available Chrome or browser
  path instead of asking the user to prove it works.
- Human final check evaluates appropriateness only: whether an objectively
  working UX, workflow, wording, or domain result is suitable for its users and
  context. Agree on the scenario, reviewer, evidence, suitability question, and
  pass/revise result before relying on that check.
- Documentation-only changes use agent inspection and applicable static checks;
  they do not require human review merely because they are not executable tests.
- There is no unverified programming branch. Missing agent-owned correctness
  evidence is an implementation gap; a pending human final check leaves only the
  specified appropriateness decision incomplete.

## DDD requirements

- Domain modeling continues through implementation: code and tests use the
  confirmed ubiquitous language within the applicable context.
- Domain invariants stay inside the domain model rather than being scattered
  through UI, transport, persistence, or orchestration code.
- External schemas and another bounded context's vocabulary cross through an
  explicit adapter or translation seam instead of becoming the internal model.
- Tactical DDD patterns are optional; use them only when they make real domain
  rules clearer. DDD compliance does not mean manufacturing entities,
  repositories, aggregates, or value objects for every change.

## Artifact requirements

- Durable artifacts live together under `docs/specs/YYYY-MM-DD-<slug>/`.
- The lifecycle uses `requirements.md`, `spec.md`, `design.md`, and
  `verification.md`; each file has one job.
- Files are created when their phase is reached, not all up front.
- Existing rules, ADRs, code, research, tickets, and visuals are linked rather
  than copied.
- There is no standalone `mini-sdd` skill. `leveraging-tasks` owns phase
  transitions and invokes the existing skills that perform each kind of work.
- Historical OpenSpec artifacts remain readable as legacy evidence but are not
  active instructions.
- Browser GUI skills are out of scope for the retained workflow; remove both
  `grill-with-web` and `open-gui`.
- Every skill description is a one-sentence trigger pointer. Workflow, exclusions,
  and handoff detail live in the skill body.

## Workflow boundaries

- Straw Boss owns app selection, dependencies, dispatch, panes, worktrees, and
  operational task state only.
- The target project's workflow owns requirements, specification, design,
  implementation, and verification after dispatch.
- ADRs remain reserved for hard-to-reverse, surprising decisions made through
  real trade-offs. `CONTEXT.md` remains a domain glossary, not a specification.
- Project instructions and native harness capabilities remain authoritative;
  the global user-root layer supplies a default protocol, not project-specific
  architecture.

## Persistence decision

- Every development task follows the same requirements, specification, design,
  implementation, and verification logic.
- Persist the four-file lifecycle only when decisions, constraints, or proof have
  future reuse: unresolved design needs persisted confirmation, public/external
  contracts or migrations affect consumers, components need coordination, or
  continuity must survive a session or handoff.
- Keep clear, localized work inline when it can be implemented and verified in
  the current run and its decisions have little future reuse. Observable behavior
  change alone is not a persistence trigger.
- A user-requested spec or an active related Mini SDD artifact remains durable.

## Capability decision

- Add `tdd`, `codebase-design`, `domain-modeling`, and `prototype` as narrowly
  triggered reusable skills.
- Extend `inspecting` with a conditional diff-review reference rather than add a
  second general review owner.
- Do not adopt Matt's issue-tracker state machine, ticket decomposition, router,
  handoff, or setup framework.

## Sources consulted

- Matt Pocock skills, commit `5b15a47f2d7150f545fbcacbfe381787fc0230dc`
- Agent OS v3, commit `cae8e664fb59a01869718c3151e0f45b7a06a2fb`
- Current `weihung-user-claude` and `straw-boss` workflows
