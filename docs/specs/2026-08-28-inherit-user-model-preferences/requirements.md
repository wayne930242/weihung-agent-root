# Inherit user model preferences

## Outcome and actors

Claude Code users keep control of the main, advisor, and dispatched worker
models. Installing this repository must not impose the former Sonnet worker pin
or replace a user's model preferences.

## In scope

- Stop installing `CLAUDE_CODE_SUBAGENT_MODEL=sonnet`.
- Remove the former repository-managed Sonnet worker pin from an existing
  installation so workers inherit the user's active model preference.
- Preserve user-owned `model`, `advisorModel`, and unrelated `env` values.
- Update current documentation and installer tests to describe and prove the
  inherited-preference behavior.
- Install the approved change into the local Claude and Codex user roots and
  verify repository source and installed state separately.

## Out of scope

- Choosing a replacement main, advisor, worker, or evaluator model.
- Disabling the advisor feature when the user has enabled it.
- Rewriting historical spec and verification records whose Sonnet references
  describe the model used for an earlier eval rather than a current policy.
- Commit, push, release, or hosted deployment.

## Scenarios

1. A fresh install creates Claude settings without `model`, `advisorModel`, or
   `CLAUDE_CODE_SUBAGENT_MODEL` and therefore inherits user choices.
2. An upgrade from the former managed configuration removes
   `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` while retaining unrelated environment
   values and user-owned model/advisor selections.
3. An install encountering a user-changed `CLAUDE_CODE_SUBAGENT_MODEL` does not
   overwrite or remove that value.
4. Uninstall removes only settings still managed by the current repository and
   preserves user-owned model/advisor selections.

## Confirmed decisions

- Main model, advisor model, and dispatched worker model are all user
  preferences; this repository does not select any of them.
- The exact former managed worker value, `sonnet`, is treated as migration state
  and removed during installation.
- Current policy documentation changes; historical evidence remains intact.

## Open questions

None.
