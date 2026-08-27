# Mini Spec 3R specification

Status: approved
Approved at: 2026-08-27
Approved from: The user's dispatched instruction of 2026-08-27, which states the
3R contract clause by clause and directs implementation without a further
confirmation round.

## Behavioral contract

### Route — declared depth

- Given a request that changes production source, when the agent grounds the
  work, then it declares the change **Inline** or **Durable** before its first
  production edit.
- Given a request that is clear, localized, implementable and verifiable in this
  run, and whose decisions have little future reuse, then Inline is correct and
  no artifact file is written.
- Given material ambiguity, scope crossing modules or sessions, a contract meant
  to last, high risk, scope expanding beyond what the user asked, or a user who
  wants to see the spec first, then the work is Durable even if it would
  otherwise look small.

### Ratify — recorded authority to edit

- Given Inline work, then the agent states one sentence of observable
  `Contract:` and records the user's explicit source-change request as
  `Authorization:`, then executes. It does not ask again for approval that
  request already granted.
- Given Durable work, then `spec.md` opens with exactly `Status`,
  `Approved at`, and `Approved from`. `Status` is `proposed` or `approved`.
- Given `Status: proposed`, then production-source editing does not begin.
  Artifact files, sandboxes, and read-only investigation remain allowed.
- Given a user reply that explicitly approves the presented spec, then and only
  then does `Status` become `approved`, `Approved at` records the date, and
  `Approved from` records the reply that granted it. The agent never advances
  the status on its own judgment, elapsed time, or a silent user.

### Result — per-requirement evidence

- Given a durable change, then `verification.md` carries a
  `Requirement | Evidence | Result` table with one row per requirement stated in
  `spec.md`.
- `Result` is `pass`, `fail`, or `unknown`. `Evidence` names the real interface
  that was exercised and what it observed.
- Given a requirement that nothing exercised, then its result is `unknown`. A
  green suite, a passing unrelated check, or the agent's own claim of completion
  is not evidence for it.
- Local verification, commit, push, CI, deployment, and browser proof stay
  distinct claims.

### Enforcement boundary

- The contract lives in the instructions the agent reads. No hook gates,
  approves, blocks, or advances any part of it; hooks stay logging and status
  surface.

## Verification contract

- A real agent-behavior eval drives a headless agent against these instructions,
  installed into an isolated home, inside a throwaway project. It asserts
  observable outcomes — files changed or not changed, artifact content — not the
  wording of the agent's narration.
- The eval covers at least three cases: an inline request executed directly, a
  durable request that stops with `Status: proposed` and an untouched production
  file, and that same durable work after explicit approval producing a
  per-requirement evidence table.
- Text and schema assertions remain only as deletion guards for load-bearing
  lines and the surface's line budget.

## Standards applied

- Progressive disclosure: the phase file states the rule, the artifact contract
  states the field shapes, and neither duplicates the other.
- Every phase keeps a checkable completion criterion.
- One source of truth per decision; the skill text is the contract, the tests
  are its guards, the eval is its proof.
- The always-loaded root prompt does not grow.

## Non-goals

- A fourth artifact file, a task engine, a status tracker, or a diary.
- Hook-based or installer-based enforcement.
- Changing the Straw Boss dispatch boundary or any other skill's ownership.
