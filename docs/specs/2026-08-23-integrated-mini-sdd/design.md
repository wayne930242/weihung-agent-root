# Integrated Mini SDD design

## Approach

Keep `leveraging-tasks` as the only global development owner. It coordinates a
grounding step followed by a five-phase lifecycle, and invokes existing
specialized skills for the work within each phase. Mini SDD is the name of this
lifecycle and artifact convention, not an invocable skill or parallel framework.

## Information hierarchy

- `AGENTS.md` and `CLAUDE.md` contain only the routing pointer needed on every
  turn.
- `skills/leveraging-tasks/SKILL.md` contains phase order, transitions, and
  completion criteria.
- `skills/leveraging-tasks/MINI-SDD.md` contains the conditional persistence
  threshold and four artifact contracts. It is read only when durable work is
  detected or a related artifact already exists.
- `skills/leveraging-tasks/DEBUGGING.md` contains the debug-only feedback-loop
  discipline. It is read only on the debug branch.
- Project rules, ADRs, reference implementations, tickets, research, and
  visuals remain their own sources of truth and are linked from artifacts.

## Phase ownership

1. **Requirements:** exploration and `grilling`; `grill-with-docs` additionally
   maintains domain terms and durable architectural decisions.
2. **Specification:** `investigating` supplies traceable facts and standards;
   `inspecting` gives scoped verdicts. `leveraging-tasks` synthesizes the
   observable contract and obtains explicit user confirmation.
3. **Design:** `leveraging-tasks` shapes interfaces, data flow, precedent,
   trade-offs, risks, and verification seams after confirmation.
4. **Implementation:** exact project skills and the harness-native plan execute
   the approved design.
5. **Verification:** `inspecting` checks Standards and Spec as separate axes;
   project tests and runtime checks provide evidence.

## Conditional engineering disciplines

- `domain-modeling` is called during Requirements or Design when terminology,
  domain boundaries, or glossary truth changes, then remains authoritative for
  names, invariants, adapters, and tests during Implementation.
- `codebase-design` is called during Spec or Design when module interfaces,
  seams, adapters, or architecture shape changes.
- `prototype` is called from Design when a throwaway experiment can settle a
  named design question.
- `tdd` is called for every programming change. Behavior changes use vertical
  red-green slices; refactors establish characterization coverage. The agent
  proves correctness through the closest available real interface, including
  Chrome/browser automation, computer use, CLI, API, or runtime harnesses. Human
  final check judges appropriateness only. Documentation uses agent review.
- `inspecting` keeps general inspection in its entrypoint and discloses fixed-point
  diff-review mechanics only for branch, PR, or change-set review.

## Routing changes

- Remove the standalone `mini-sdd` skill and its installer assertions.
- Remove both `grill-with-web` and `open-gui`; the retained workflow has no
  browser GUI skill or supporting runtime.
- Make `grill-with-docs` return confirmed requirements to its caller rather than
  hand off to another framework.
- Trim generic no-op prose from `providing-knowledge` and move the optional scout
  branch out of `investigating`'s main path.
- Remove forced commit behavior from final QA; Git mutations remain separately
  authorized delivery actions.
- Rewrite every retained skill description as one short trigger-only sentence.

## Complete skill disposition

| Skill | Decision | Boundary |
|---|---|---|
| `assuring-quality` | Keep and simplify | Own final exploratory QA and evidence; source fixes return through `leveraging-tasks`; no forced commits. |
| `grill-me` | Keep thin | Explicit user entry to `grilling`; no separate behavior. |
| `grilling` | Keep | Own the decision-tree interview and user confirmation; return confirmed requirements to its caller. |
| `grill-with-docs` | Keep and adjust | Add domain glossary and sparse ADR recording; return requirements directly to the caller. |
| `grill-with-web` | Remove | The user no longer wants browser-based grilling. |
| `inspecting` | Keep | Own scoped evidence verdicts; contribute standards and verification findings when called by development. |
| `investigating` | Keep and simplify | Own traceable fact gathering; remove the optional scout ceremony from its main contract. |
| `leveraging-tasks` | Keep and narrow | Sole owner of source-changing development and Mini SDD phase transitions. |
| `mini-sdd` | Remove as a skill | Replace with a conditional plain reference under `leveraging-tasks`. |
| `open-gui` | Remove | The user does not need the browser GUI runtime. |
| `providing-knowledge` | Keep and simplify | Preserve mental-model-first answers; remove default-model no-ops. |
| `refining-from-complaints` | Keep and adjust | Own complaint-to-confirmed-root-cause shaping; every source fix hands off to `leveraging-tasks`. |
| `reflecting-to-root` | Keep but make explicit | Proposal-first user-invoked reflection; write rules only after user approval. |
| `writing-great-skills` | Keep | Its length is conditional reference, not always-loaded routing; retain its progressive-disclosure contract. |
| `tdd` | Add | Mandatory for programming changes; own red-green or characterization coverage, agent-operated correctness, and the separate human appropriateness checkpoint. |
| `codebase-design` | Add | Supply deep-module, interface, seam, adapter, locality, and testability discipline. |
| `domain-modeling` | Add | Actively reconcile domain terminology, scenarios, code, glossary, and qualifying ADRs. |
| `prototype` | Add | Answer a named design question with disposable evidence and return the verdict to Design. |

## Durable artifact lifecycle

The phase logic always applies, but files exist only when their decisions,
constraints, or proof have future reuse. Clear localized work remains inline
even when it changes behavior. Durable artifacts live under
`docs/specs/YYYY-MM-DD-<slug>/` and appear only as phases are reached:

- `requirements.md`: outcome, actors, scope, scenarios, decisions, open questions
- `spec.md`: observable contract, edge cases, constraints, applied standards,
  evidence links, confirmation
- `design.md`: approach, interfaces/data flow, precedent, trade-offs, risks,
  verification plan
- `verification.md`: requirement-to-evidence mapping, results, deviations, gaps

There is no `tasks.md` or implementation diary. Code and native plans represent
execution; `verification.md` records what was proven.

## Verification plan

- Search active instructions for standalone Mini SDD, `grill-with-web`,
  `open-gui`, and active OpenSpec routing.
- Run install, uninstall, hooks, Codex hooks, and bootstrap tests.
- Run `git diff --check` in both affected repositories.
- Review the final diff separately against repository standards and this spec.
