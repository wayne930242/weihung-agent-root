# Integrated Mini SDD artifact contract

Mini SDD is the durable branch of `leveraging-tasks`, not a skill, task engine,
or dispatcher.

## Persistence threshold

Artifact creation is a future-value decision, not a consequence of entering
`leveraging-tasks` or changing observable behavior. Create or resume
`docs/specs/YYYY-MM-DD-<slug>/` when any condition applies:

- a decision, constraint, or proof must guide future work beyond this run
- unresolved design needs explicit confirmation and persisted context
- a public/external contract or migration affects downstream consumers
- multiple components need a shared compatibility or coordination record
- continuity is required across compaction, another session, or a handoff
- the user asks for a spec or durable design
- an active related Mini SDD artifact already owns the change

Keep work inline when requirements are clear, impact is localized,
implementation and verification fit this run, and its decisions have little
future reuse. Inline work may add or change observable behavior and creates no
artifact folder.

## Phase files

Create each file only when its phase is reached.

### `requirements.md`

- Outcome and actors
- In scope and out of scope
- Concrete scenarios
- Confirmed decisions
- Open questions; empty before specification completes

### `spec.md`

- Observable behavior and edge cases
- Compatibility constraints and non-goals
- Applied standards: path or URL plus impact on this change
- Evidence and precedent pointers
- Agent-owned correctness strategy and interface
- Any separate human-owned appropriateness question
- User confirmation and date

### `design.md`

- Chosen approach
- Interfaces and data flow affected
- Existing precedent or reference implementation
- Decisions, trade-offs, and risks
- Selected correctness method and its executable or operational seam
- Any agreed human final check for appropriateness

This is the implementation-ready handoff. A straightforward design may be short;
it still names the relevant precedent and verification seam.

### `verification.md`

- Requirement-to-evidence mapping
- Automated, runtime, and agent-operated interface results
- Human appropriateness verdicts when applicable
- Deviations from the confirmed spec or design
- Unresolved gaps and their impact
- Separate commit, push, CI, deployment, and browser evidence when applicable
- Separate automated results, interface observations, operational evidence,
  human appropriateness verdicts, and unresolved gaps

## Update rules

- Link to project instructions, ADRs, code, research, tickets, and visuals rather
  than duplicating them.
- Update the owning phase file when new information changes it.
- A change to user intent or observable behavior returns to specification and
  user confirmation.
- Native plans own execution sequencing. Do not create `tasks.md` or an
  implementation diary.
