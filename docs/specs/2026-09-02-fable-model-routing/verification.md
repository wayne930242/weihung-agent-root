# Fable model routing verification

## Requirement evidence

| Requirement | Evidence | Result |
|---|---|---|
| Repository settings select `claude-fable-5-1`, preserve cross-session inbound, and add no advisor or worker pin | `python3 -m json.tool config/claude-settings.json`; direct source inspection | pass |
| `CLAUDE.md` is the canonical model-routing policy for fragmentary work, highest-complexity work, pure code writing, and the default model | `bash tests/prompts.sh`; `claude_model_routing_is_canonical` checks every required route | pass |
| The prompt carries the authorized Straw Boss repair, bump, push, reload, and resume lifecycle | `bash tests/prompts.sh`; direct diff review of `Model Work Routing` | pass |
| Fresh and upgrade installs write the exact main model while preserving unrelated user state | `bash tests/install.sh`; all fresh, upgrade, advisor, worker-model, environment, hook, and link cases passed | pass |
| Uninstall remains value-sensitive and preserves user-owned model and advisor values | `bash tests/uninstall.sh`; full suite passed | pass |
| Current installer help and README describe the exact model and routing authority | Static search and independent diff review found no stale active Opus-main description | pass |
| Real installed settings and prompt match the repository | `bash scripts/install.sh` exited 0; focused inspection observed `model=claude-fable-5-1`, `crossSessionInbound=accept`, no advisor or worker pin, and `~/.claude/CLAUDE.md` resolving to this repo with every required routing phrase | pass |
| Claude Code accepts the exact Fable 5.1 model name and Fable supplies a 1M context by default | Claude Code 2.1.258 accepted `--model claude-fable-5-1`; the earlier runtime probe resolved canonical `claude-fable-5-1` with `contextWindow=1000000`; Anthropic's current migration guidance states that Fable 5 uses a 1M context window by default | pass |

## Red and green evidence

- Red: initial focused tests observed the old `opus[1m]` setting and missing
  `Model Work Routing` section.
- Red: after the final correction, focused tests expected
  `claude-fable-5-1` and observed the prior `[1m]`-suffixed value and prompt.
- Green: focused installer and prompt tests passed after implementation.
- Regression: full `tests/prompts.sh`, `tests/install.sh`, and
  `tests/uninstall.sh` suites exited 0.

## Additional validation

- `bash -n scripts/install.sh scripts/uninstall.sh tests/install.sh tests/uninstall.sh tests/prompts.sh` passed.
- Both managed Claude JSON fragments parsed successfully.
- `git diff --check` passed.
- Independent diff review found no conflicting model route or stale active
  Opus-main documentation.
- The earlier model-resolution probe reached canonical `claude-fable-5-1`
  with a 1M context but stopped before completing its reply because the imposed
  USD 0.10 limit was lower than the reported USD 0.13974575 usage.
- A no-suffix parse probe accepted `claude-fable-5-1` and entered the runtime;
  its deliberately tiny budget stopped before the selected model was called,
  costing USD 0.000934. No second full paid probe was run.

## Human appropriateness

The final exact model string comes from the user's latest correction:
`claude-fable-5-1` is both the main model and the highest-complexity model.

## Deviations

None from the approved observable behavior.

## Unresolved gaps

- No commit or push was performed because the request covered modification and
  installation, not repository delivery.
- `~/projects/straw-boss` was not modified because no confirmed Straw Boss
  defect was part of the requested final work.
