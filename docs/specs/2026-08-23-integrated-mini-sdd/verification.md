# Integrated Mini SDD verification

Verified: 2026-08-23

## Requirement-to-evidence mapping

| Requirement | Evidence | Result |
|---|---|---|
| One development owner embeds Mini SDD | `AGENTS.md`, `CLAUDE.md`, and `skills/leveraging-tasks/SKILL.md` route source-changing work through `leveraging-tasks` | Pass |
| Durable requirements, spec, design, and verification remain traceable | `skills/leveraging-tasks/MINI-SDD.md` defines the threshold, four phase files, and update rules | Pass |
| Specification precedes implementation and requires user confirmation | The Spec phase blocks production-source editing until explicit confirmation | Pass |
| Debugging begins with executable feedback before specification | The Ground phase loads `DEBUGGING.md` and establishes its red-capable loop before diagnosis | Pass |
| No parallel task engine or implementation diary | Native plans own sequencing; `tasks.md` and implementation diaries are explicitly excluded | Pass |
| Straw Boss remains dispatch-only | Its `work-on`, `shipping-task`, plan mechanics, and architecture changes defer development and SDD to the target app after entry | Pass |
| No active OpenSpec route | Active root instructions, rules, skills, and tests contain no `OpenSpec` or `opsx` route; historical artifacts are archived | Pass |
| Browser GUI workflow removed | `skills/grill-with-web` and `skills/open-gui` are absent; active paths contain no references | Pass |
| Complaint workflow is preserved | `refining-from-complaints` owns complaint-to-root-cause confirmation and returns source changes to `leveraging-tasks` | Pass |
| TDD is mandatory for every programming change | `tdd` requires red-green feedback for behavior changes and characterization coverage for behavior-preserving refactors | Pass |
| Correctness remains agent-owned | `tdd` requires the agent to exercise the closest credible interface, including tests, CLI, API, runtime, Chrome/browser automation, or computer use | Pass |
| Human review owns appropriateness only | `tdd/HUMAN-FINAL-CHECK.md` requires objective correctness evidence before asking whether the working result is suitable | Pass |
| Programming cannot close without correctness evidence | Missing agent-owned evidence remains an implementation gap and cannot be replaced by a human verdict | Pass |
| Module design has a shared discipline | `codebase-design` defines depth, interface burden, seams, adapters, deletion test, locality, and test surface | Pass |
| Domain modeling continues through implementation | `domain-modeling` aligns ubiquitous language, invariants, bounded contexts, adapter translations, code, and tests | Pass |
| Prototypes answer one disposable design question | `prototype` requires a falsifiable question, explicit oracle, disposal plan, and recorded verdict in Design | Pass |
| Diff review has a stable evidence boundary | `inspecting/DIFF-REVIEW.md` covers merge-base, committed and working-tree changes, relevant untracked files, and independent Standards/Spec verdicts | Pass |
| Skill descriptions are trigger-only | All 15 retained descriptions are one line, one sentence, and at most 120 characters | Pass |

## Automated results

- All 15 retained skills passed Codex `quick_validate.py`.
- `tests/install.sh`: pass; the local install linked the four new skills in both
  tool roots, with explicit Codex assertions for each.
- `tests/uninstall.sh`: pass.
- `tests/hooks.sh`: pass.
- `tests/codex_hooks.sh`: pass.
- `tests/bootstrap.sh`: pass. This test clones the committed remote baseline, so
  it proves bootstrap behavior but is not evidence of the uncommitted local
  skill removals.
- `git diff --check`: pass in `weihung-user-claude` and `straw-boss`.
- Active-reference searches for removed GUI skills and OpenSpec routing: no
  matches.
- Semantic assertions for mandatory TDD, agent-owned interface verification,
  human appropriateness, DDD implementation continuity, working-tree diff
  coverage, conditional skill routing, and short descriptions: pass.

## Review verdict

- **Standards:** pass. Routing has one owner, descriptions are minimal triggers,
  conditional detail uses plain references, and Git/automation/delegation
  boundaries remain in their designated files.
- **Spec:** pass. The implemented lifecycle, persistence threshold, skill
  boundaries, engineering disciplines, correctness/appropriateness split, GUI
  removals, and Straw Boss handoff match the confirmed contract.

## Delivery evidence

- Local verification: complete.
- Commit: not performed.
- Push: not performed.
- CI: not run.
- Deployment: not performed.
- Browser proof: not applicable.
