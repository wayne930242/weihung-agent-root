# Durable artifact contract

Read this when `leveraging-tasks` classifies work as durable. The threshold
itself lives in [SKILL.md](SKILL.md); this file only says what each file holds.

Artifacts live in `docs/specs/YYYY-MM-DD-<slug>/`. Create each file when its
phase is reached, not up front. Link to project instructions, ADRs, code,
research, tickets, and visuals rather than copying them.

## `requirements.md`

Outcome and actors; in and out of scope; concrete scenarios; confirmed
decisions; open questions, empty before the spec is confirmed.

## `spec.md`

Opens with the approval header, then observable behavior and edge cases;
compatibility constraints and non-goals; applied standards with their impact;
evidence and precedent links; the agent-owned correctness strategy and its
interface; any separate human appropriateness question.

```
Status: proposed | approved
Approved at: <date the user approved, empty while proposed>
Approved from: <the user reply that approved it, empty while proposed>
```

## `design.md`

Chosen approach; interfaces and data flow affected; existing precedent;
decisions, trade-offs, and risks; the selected correctness method and its
executable or operational seam. This is the implementation-ready handoff — a
straightforward design may be short, but it still names precedent and seam.

## `verification.md`

One `Requirement | Evidence | Result` row per requirement in `spec.md`, where
`Result` is `pass`, `fail`, or `unknown`; then human appropriateness verdicts;
deviations from the confirmed spec or design; unresolved gaps and their impact.
Keep local verification, commit, push, CI, deployment, and browser proof as
separate claims.

## Updates

Update the owning phase file when new information changes it. A change to user
intent or observable behavior returns to the Spec phase and to user
confirmation.
