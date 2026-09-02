# ADAAV decision-first Mini SDD design

## Chosen approach

Keep `leveraging-tasks` as the single source-changing owner and reorganize its
existing lifecycle under ADAAV:

1. **Align** — restate intent; classify Inline or Durable; capture Inline
   contract and authorization.
2. **Advance** — for Durable work, run Decision → Spec → Design. The Decision
   step invokes `grill-with-docs`, which writes the exploratory decision record
   and reaches `grilling` only for open consequential user choices. Spec keeps
   the existing explicit approval gate. Design makes implementation mechanical.
3. **Anchor** — state the simplest credible reality contact and checkpoint
   before the first production edit.
4. **Act** — implement through the target project's native practices.
5. **Verify** — exercise the anchor and record per-requirement results.

Inline work follows Align → Anchor → Act → Verify. This keeps the useful short
path while giving both branches the same vocabulary.

## Information hierarchy and ownership

| Concern | Single source of truth |
|---|---|
| ADAAV transitions and completion criteria | `skills/leveraging-tasks/SKILL.md` |
| Durable artifact shapes and legacy resumption | `skills/leveraging-tasks/MINI-SDD.md` |
| Decision exploration and conditional interview | `skills/grill-with-docs/SKILL.md` |
| Interactive decision-tree mechanics | `skills/grilling/SKILL.md` |
| User-facing workflow explanation | `README.md` |
| Static deletion guards | `tests/prompts.sh` |
| Installed runtime behavior | `evals/mini-spec-3r.sh` |

Related skills use “decision input” and the Advance phase vocabulary where
they hand findings or domain knowledge back to `leveraging-tasks`. They do not
repeat the artifact format.

## Decision document

`decision.md` replaces `requirements.md` for new Durable folders and records:

- outcome, actors, boundaries, and scenarios
- `Question | Answer | Basis | Status` for every consequential branch exposed
  during exploration
- confirmed decisions
- open consequential decisions

Statuses are `grounded`, `confirmed`, or `open`. A grounded answer comes from
the request, code, project documentation, or an existing durable decision. A
confirmed answer comes from the user. An open row identifies what must reach
`grilling`. `spec.md` is created only when no row remains open.

Existing folders with `requirements.md` retain that file as their decision
artifact. Resume logic updates the existing artifact and does not create a
parallel replacement.

## Skill interaction

`leveraging-tasks` invokes `grill-with-docs` for the Durable Decision step and
supplies the active decision artifact. `grill-with-docs` explores the decision
tree, resolves facts from sources, and writes all known Q&A first. If open
user-owned decisions remain, it passes only that frontier to `grilling` and
writes the confirmed answers back. It then returns the completed decision
artifact to the same `leveraging-tasks` run.

`grilling` remains the generic interactive owner. Its output becomes confirmed
answers and decisions written to a caller-provided decision artifact, rather
than requirements handed to a separate lifecycle.

No standalone ADAAV or Mini SDD skill is added. This avoids a second owner and
keeps the model-invoked surface small.

## Verification design

### Static contract

Extend `tests/prompts.sh` to require:

- the exact ADAAV sequence and Decision → Spec → Design mapping
- new Durable work routing through `grill-with-docs`
- `decision.md` and its question table responsibilities
- conditional interviewing based on open consequential decisions
- explicit legacy `requirements.md` resumption
- the unchanged approval and evidence rules

Retain the existing line budgets where pruning makes that practical; adjust a
budget only when the new live contract cannot fit without weakening it.

### Real installed behavior

Extend the durable proposal case in `evals/mini-spec-3r.sh`. Its prompt is
decision-complete, so the installed agent must:

1. create `decision.md` before reaching the spec gate
2. record exploratory questions, answers, bases, and resolved statuses
3. create no new `requirements.md`
4. reach `spec.md` at `Status: proposed` without stalling for product answers
5. leave production source untouched until approval
6. resume after approval, implement, and write per-requirement evidence

The approval question is distinct from interrogation and remains expected.
An agent-level authentication or usage-limit error fails the turn before
behavioral assertions run.

## Implementation order

1. Add static assertions and behavior-eval assertions; run focused static tests
   to prove the current wording is red.
2. Rewrite `leveraging-tasks`, `MINI-SDD.md`, `grill-with-docs`, and `grilling`.
3. Align related skill handoffs and `README.md` terminology.
4. Run focused and full repository tests plus shell/static checks.
5. Run the real agent behavior eval against the installed throwaway home.
6. Run the repository installer for the real user root and verify both Claude
   and Codex skill links resolve to the updated files.

## Trade-offs and risks

- A decision document can become ceremony when questions are trivial. Requiring
  it only for Durable work and allowing grounded answers keeps Inline work
  artifact-free and avoids interviews that add no information.
- “Obvious” can hide model assumptions. The `Basis` column makes each skipped
  question auditable and sends unsupported consequential answers to the user.
- Renaming all historical artifacts would create noisy, low-value churn. Legacy
  resumption preserves continuity while the new creation rule converges future
  work on `decision.md`.
- ADAAV could duplicate Mini SDD terminology. Treating Decision → Spec → Design
  as the content of Advance makes ADAAV the sole top-level sequence and Mini SDD
  its durable elaboration.

## Domain decision

ADAAV is the canonical name for the personal source-changing loop. “Advance”
means preserving and advancing the established context through decisions,
specification, and design; it is not a handoff to a new owner. The approved spec
is the durable record for this workflow term, so no parallel glossary or ADR is
created.
