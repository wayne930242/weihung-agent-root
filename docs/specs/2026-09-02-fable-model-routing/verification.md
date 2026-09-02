# Claude model routing verification

## Requirement evidence

| Requirement | Evidence | Result |
|---|---|---|
| Repository settings select `opus[1m]`, preserve cross-session inbound, and add no advisor or worker pin | `python3 -m json.tool config/claude-settings.json`; focused install test observed `model=opus[1m]` | pass |
| `CLAUDE.md` keeps directly instructed simple work with the orchestrator and delegates other fragments through Straw Boss or a subagent | `bash tests/prompts.sh`; `claude_model_routing_is_canonical` checks both branches and rejects the former universal-dispatch sentence | pass |
| The ordered work routes use the orchestrator's current model for highest-complexity and remaining work, Codex for document writing, and Sonnet for code writing, investigation, and lookup | `bash tests/prompts.sh`; focused route assertions all passed | pass |
| The prompt carries the authorized Straw Boss repair, bump, push, reload, and resume lifecycle | `bash tests/prompts.sh`; direct diff review of `Model Work Routing` | pass |
| `Orchestrator 權限移交` recommends Fable 5.1 only for extreme complexity judged by Opus, waits for user approval, starts Fable `boss-say` in an independent Herdr pane, then closes the original pane | `bash tests/prompts.sh orchestrator_authority_handoff_is_user_gated`; whitespace-normalized inspection of the real installed prompt observed the complete ordered flow | pass |
| Fresh and upgrade installs write the exact main model while preserving unrelated user state | `bash tests/install.sh`; all fresh, upgrade, advisor, worker-model, environment, hook, and link cases passed | pass |
| Uninstall remains value-sensitive and preserves user-owned model and advisor values | `bash tests/uninstall.sh`; full suite passed | pass |
| Current installer help and README describe the Opus 1M default and dynamic orchestrator routing | Static search and diff review found no stale active Fable-default description | pass |
| Real installed settings and prompt match the repository | `bash scripts/install.sh` exited 0; focused inspection observed `model=opus[1m]`, `crossSessionInbound=accept`, no advisor, the repository prompt symlink, and every new routing phrase | pass |

## Red and green evidence

- Red: the focused prompt test required direct execution for a simple user
  instruction and observed the former universal-dispatch rule.
- Red: focused installer and prompt tests expected `opus[1m]` plus dynamic
  orchestrator inheritance and observed the previous Fable setting and route.
- Red: the focused authority-handoff test observed that the named section was
  absent before implementation.
- Green: focused prompt and fresh-install tests passed after implementation.
- Regression: full `tests/prompts.sh`, `tests/install.sh`, and
  `tests/uninstall.sh` suites exited 0.

## Additional validation

- `bash -n scripts/install.sh scripts/uninstall.sh tests/install.sh tests/uninstall.sh tests/prompts.sh` passed.
- Both managed Claude JSON fragments parsed successfully.
- `git diff --check` passed before the real install.
- The expected negative conflict cases printed errors during installer and
  uninstaller tests while both suites still exited 0.
- Real installation reported success and the focused post-install assertions
  passed without exposing unrelated user settings.
- The first post-install line-oriented search could not match wrapped prose;
  whitespace-normalized inspection then observed every required handoff phrase.

## Human appropriateness

The exact `opus[1m]` default comes from the user's latest correction. Inheriting
the orchestrator's current model for the most complex work preserves the user's
ability to switch a work session to Fable 5.1 without another prompt edit. The
ordered routes also resolve overlap deterministically: highest complexity,
document writing, Sonnet work types, then the current orchestrator model.
The named authority handoff keeps the model recommendation separate from the
irreversible pane transition, which remains gated by explicit user approval and
a running destination `boss-say`.

## Deviations

None from the approved observable behavior.

## Unresolved gaps

- No commit or push was performed for this revision because the latest requests
  covered modification and installation, not repository delivery.
- `~/projects/straw-boss` was not modified because no confirmed Straw Boss
  defect was part of the requested work.
