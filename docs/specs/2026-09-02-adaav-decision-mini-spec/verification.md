# ADAAV decision-first Mini SDD verification

## Requirement evidence

| Requirement | Evidence | Result |
|---|---|---|
| 1. `leveraging-tasks` names and follows ADAAV, with Advance carrying Decision → Spec → Design | Installed Claude and Codex `leveraging-tasks/SKILL.md` both expose the exact ADAAV sequence and mapping; `tests/prompts.sh` passed. The headless agent could not exercise the sequence because its turn was blocked before work began. | unknown |
| 2. New Durable work creates `decision.md` with the complete decision record before `spec.md` | `MINI-SDD.md` defines the artifact and table; the behavior eval checks its existence and write order. No authenticated behavior turn reached artifact creation. | unknown |
| 3. Grounded consequential answers return without an interview | Installed `grill-with-docs/SKILL.md` returns directly when the document has no open consequential decision; static deletion guards passed. No agent turn exercised this branch. | unknown |
| 4. Open user-owned decisions reach only the unresolved `grilling` frontier and return to Advance | `grill-with-docs/SKILL.md`, `grilling/SKILL.md`, and `leveraging-tasks/SKILL.md` carry the handoff and continuation contract; static guards passed. No agent turn exercised this branch. | unknown |
| 5. `spec.md` is proposed only after decisions close, and production waits for explicit approval | The skills retain the proposed/approved fields and production-edit gate; existing approval deletion guards passed. The changed installed prompt did not reach this checkpoint in the behavior eval. | unknown |
| 6. Approved Durable work completes Design → Anchor → Act → per-requirement Verify | `leveraging-tasks/SKILL.md` and `MINI-SDD.md` retain the implementation-ready design and evidence contracts; static guards passed. The approval turn could not run against the changed prompt. | unknown |
| 7. Inline work remains artifact-free and follows Align → Anchor → Act → Verify | The Inline contract remains in `leveraging-tasks/SKILL.md` and its eval case remains present. The changed prompt was not exercised by an authenticated headless turn. | unknown |
| 8. Historical `requirements.md` folders resume in place while new folders use `decision.md` | `MINI-SDD.md`, README, and prompt guards state the compatibility rule. No live legacy-resumption scenario exercised it. | unknown |
| 9. Claude and Codex receive the workflow through managed skill links without a hook engine | `bash scripts/install.sh` exited 0; all four real user-root links for `leveraging-tasks` and `grill-with-docs` resolve to this repository; hook-isolation, install, uninstall, bootstrap, and WSL installer tests passed. | pass |
| 10. Documentation, static tests, and real behavior eval carry the same contract | README, skills, prompt guards, and eval assertions align; all static suites passed. The real eval was blocked before ADAAV behavior, so the runtime part has no result. | unknown |

## Supporting checks

| Check | Evidence | Result |
|---|---|---|
| Static prompt contract | `bash tests/prompts.sh` | pass |
| Claude/Codex installation lifecycle | `tests/install.sh`, `tests/uninstall.sh`, `tests/bootstrap.sh`, and `tests/install_codex_desktop_wsl.sh` all exited 0 | pass |
| Hook suites | `tests/hooks.sh` and `tests/codex_hooks.sh` both exited 0 | pass |
| Shell and patch integrity | `bash -n` across eval, tests, and scripts; `git diff --check` | pass |
| Real user-root installation | Installer exited 0; Claude and Codex skill symlinks and their ADAAV content were read back successfully | pass |
| Real agent behavior | Isolated eval stopped at `Not logged in`; a real-config Claude probe reached the service but returned session limit until 13:30 Asia/Taipei. No prompt behavior was exercised. | unknown |

## Independent diff review

### Standards

Pass. The diff keeps one source-changing owner, one top-level ADAAV sequence,
the durable artifact format behind `MINI-SDD.md`, and conditional interview
behavior in `grill-with-docs`. The review found and corrected the README rule
count, a legacy-artifact ambiguity, and the resolved-decision return condition.
No remaining documented-standard violation was observed.

### Spec

Needs attention only for runtime evidence. Every approved behavior is represented
in the skills, documentation, static guards, and eval assertions; requirements
1–8 and 10 remain `unknown` because the real agent never crossed its
authentication/session boundary. Requirement 9 has direct installation evidence.

## Human appropriateness

The user approved the observable specification with `批准`. The implementation
keeps obvious answers as grounded Q&A, asks only open consequential decisions,
and continues through the same Mini SDD owner under ADAAV.

## Deviations and unresolved gaps

- The real behavior checkpoint is incomplete. Re-run
  `bash evals/mini-spec-3r.sh` with an authenticated headless Claude environment
  after the session limit resets, then replace the affected `unknown` rows with
  the observed results.
- No commit, push, CI, or release was requested or performed. These remain
  distinct from the completed local installation.
