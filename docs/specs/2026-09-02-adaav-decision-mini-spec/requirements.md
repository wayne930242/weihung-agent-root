# ADAAV decision-first Mini SDD requirements

## Outcome and actors

The personal development workflow uses ADAAV — Align, Advance, Anchor,
Act, Verify — as its visible sequence. For durable work, the workflow writes a
decision document containing exploratory questions and their answers before it
states the observable specification. The agent asks the user only about
consequential decisions whose answers are not already evident from the request,
project facts, or existing decisions.

The primary actor is the user directing source-changing work. The agent owns
fact-finding, recording the decision state, advancing the Mini SDD lifecycle,
implementation, and evidence collection. The user owns unresolved consequential
choices and approval of the observable specification.

## In scope

- Make ADAAV the named top-level development loop in `leveraging-tasks`.
- Integrate `grill-with-docs` into the durable Mini SDD decision phase.
- Replace the durable `requirements.md` artifact with `decision.md` for new work.
- Give `decision.md` exploratory questions, answers, their basis, confirmed
  decisions, and unresolved consequential decisions.
- Skip interviewing when every consequential answer is evident and recorded.
- Continue from the decision document into specification, design,
  implementation, and verification without restarting ownership or context.
- Update repository guidance, static prompt-contract tests, and real behavior
  evaluation coverage that encode the existing Mini SDD artifact contract.
- Preserve compatibility with active historical spec folders that contain
  `requirements.md`.

## Out of scope

- Renaming existing historical `requirements.md` files.
- Adding a task tracker, diary, or a fifth durable artifact.
- Changing deployment, model routing, orchestration, or approval policy.
- Making `grill-with-docs` responsible for implementation.

## Concrete scenarios

1. A durable request already answers every consequential question. The agent
   records exploratory questions and grounded answers in `decision.md`, performs
   no interview, prepares `spec.md`, and continues through the approval gate.
2. A durable request leaves a consequential choice open. The agent records what
   is known, asks only the current decision-tree frontier, writes the confirmed
   answer back to `decision.md`, then continues to `spec.md`.
3. An existing Mini SDD folder contains `requirements.md`. The agent resumes it
   in place instead of forcing a migration, while new durable work uses
   `decision.md`.
4. Inline work remains artifact-free while still expressing ADAAV through its
   Alignment, continuation context, Reality anchor, implementation, and
   requirement-level verification.

## Confirmed decisions

- ADAAV means Align → Advance → Anchor → Act → Verify.
- `decision.md` replaces `requirements.md` for newly created durable work.
- Exploratory questions are always made explicit in the decision document;
  user questioning is conditional on consequential uncertainty.
- The existing `spec.md` user-approval gate remains the boundary before
  production edits.
- Historical artifacts remain valid and resumable.

## Open questions

None block the observable specification.
