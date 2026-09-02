# ADAAV decision-first Mini SDD specification

Status: approved
Approved at: 2026-09-02
Approved from: 批准

## Observable contract

1. `leveraging-tasks` names and follows the ADAAV sequence: Align → Advance →
   Anchor → Act → Verify. Advance carries the durable Mini SDD sequence of
   Decision → Spec → Design, so the development owner and accumulated context
   continue across every phase.
2. Every new durable folder creates `decision.md` before `spec.md`; a resumed
   legacy folder continues with its existing `requirements.md`. The active
   decision artifact records the intended outcome, scope, exploratory questions,
   each known answer and its basis, confirmed decisions, and open consequential
   decisions.
3. `grill-with-docs` resolves questions from the user's request, project facts,
   and existing decisions first. When all consequential answers are evident,
   it records them and returns directly without invoking an interview.
4. When a consequential user-owned answer remains open, `grill-with-docs`
   invokes `grilling` only for the unresolved design-tree frontier, records the
   confirmed answer in `decision.md`, and returns to the same Advance phase.
5. Advance may write `spec.md` only after no open decision blocks observable
   behavior. The existing `Status: proposed` approval gate remains: production
   source stays untouched until the user explicitly approves the specification.
6. After approval, Advance records the implementation-ready design; Anchor
   fixes the simplest credible reality contact and checkpoint; Act implements;
   Verify maps every specification requirement to observed evidence and a
   `pass`, `fail`, or `unknown` result.
7. Inline work creates no durable artifacts. It follows ADAAV by stating
   Alignment and its authorized observable contract, proceeding directly to a
   Reality anchor, implementing, and verifying.
8. Existing durable folders containing `requirements.md` remain valid and are
   resumed in place. New durable folders use `decision.md`; historical
   artifacts are not renamed.
9. Installed Claude and Codex environments receive this behavior through the
   repository-managed skill links, without introducing hooks or a separate
   workflow engine.
10. Repository documentation, static prompt-contract tests, and the real
    behavior eval describe and exercise the same ADAAV and decision-document
    contract.

## Decision document shape

`decision.md` contains these responsibilities without prescribing decorative
formatting:

- outcome and actors
- in-scope and out-of-scope boundaries
- concrete scenarios
- exploratory `Question | Answer | Basis | Status` entries
- confirmed decisions
- open consequential decisions, empty before `spec.md` is proposed

Question status distinguishes a grounded answer from a user-confirmed answer
and an open decision. The basis points to the request, source evidence, or an
existing durable decision instead of repeating it.

## Edge cases

- A question with an obvious factual answer is answered from its source and is
  not presented as a user decision.
- A reversible implementation detail with clear precedent does not trigger an
  interview; it belongs in design.
- A product, scope, compatibility, architecture, or irreversible trade-off
  whose answer is not evident remains open and is asked.
- Discovering a new consequential decision during spec or design returns to
  `decision.md`; it does not start a second workflow.
- A change to approved observable behavior returns `spec.md` to proposal and
  user confirmation under the existing approval rule.
- A legacy `requirements.md` folder is updated in its existing artifact rather
  than gaining a parallel `decision.md` solely for migration.

## Compatibility constraints

- Preserve the current Inline/Durable threshold and explicit authorization
  behavior.
- Preserve the current production-edit approval boundary.
- Preserve `spec.md`, `design.md`, and `verification.md` field contracts.
- Preserve requirement-level evidence and the distinction between local tests,
  commit, push, CI, deployment, browser proof, and human judgment.
- Keep Mini SDD as a reference owned by `leveraging-tasks`, not a separately
  invocable skill.
- Keep prompt behavior in skills and documentation; hooks remain outside the
  workflow contract.

## Non-goals

- Migrating historical spec directories.
- Adding `tasks.md`, agent state, a diary, or a fifth durable artifact.
- Making all source changes durable.
- Asking the user to confirm answers already established by the request or
  evidence.
- Moving specification, design, implementation, or verification ownership into
  `grill-with-docs`.

## Applied standards

- `AGENTS.md`: source-changing work remains owned by `leveraging-tasks`, and
  Alignment plus Reality anchor precede the first production edit.
- Positive instruction style: describe the intended decision path directly;
  hard approval boundaries remain explicit guardrails.
- `writing-great-skills`: keep one source of truth for each rule, disclose the
  durable artifact format through `MINI-SDD.md`, and use checkable phase
  completion criteria.
- Existing Mini SDD precedent: retain conditional persistence, explicit
  ratification, and requirement-specific result evidence.

## Evidence and precedent

- `skills/leveraging-tasks/SKILL.md` owns source-changing phase transitions.
- `skills/leveraging-tasks/MINI-SDD.md` owns durable artifact shapes.
- `skills/grill-with-docs/SKILL.md` currently connects interviewing with domain
  documents and is the integration seam for decision-first exploration.
- `tests/prompts.sh` protects load-bearing prompt contracts and line budgets.
- `evals/mini-spec-3r.sh` exercises installed agent behavior against a real
  throwaway project and preserves the approval transition across turns.

## Reality anchor and checkpoint

Reality anchor: the installed `leveraging-tasks` and `grill-with-docs` skills
operated by a real headless agent in the existing Mini Spec behavior harness.

Checkpoint: static prompt tests pass; the proposal turn for a decision-complete
durable request creates `decision.md` with grounded exploratory answers and
`spec.md` at `Status: proposed` while production source is unchanged; the
approval turn implements and records per-requirement evidence. Repository-wide
install and shell checks remain separate supporting evidence.
