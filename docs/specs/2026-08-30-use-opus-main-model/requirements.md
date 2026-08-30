# Use Opus as the Claude main model

## Outcome and actors

Claude Code users installing this repository receive Opus as the explicit main
model without a repository-managed advisor selection.

## In scope

- Change the repository-managed Claude main model from `sonnet` to `opus`.
- Remove the repository-managed `advisorModel` setting while keeping
  `crossSessionInbound=accept`.
- Remove the formerly managed `advisorModel=opus` value from an existing local
  installation without deleting a user-selected non-Opus advisor value.
- Update current installer tests and documentation to describe Opus main with no
  repository-managed advisor.
- Install the updated settings into the real Claude user root and verify source
  and installed state separately.

## Out of scope

- Adding or changing a dispatched worker-model environment override.
- Changing Codex role models.
- Rewriting historical specs that accurately record earlier Sonnet/Opus work.
- Commit, push, release, or hosted deployment.

## Scenarios

1. A fresh install writes `model=opus` without `advisorModel`.
2. An upgrade replaces the former repository-managed `model=sonnet` value with
   `model=opus`, removes the former managed `advisorModel=opus` value, and
   retains the cross-session setting.
3. The legacy `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` migration continues to remove
   only that obsolete managed worker pin.
4. Installation and uninstallation preserve a user-selected non-Opus advisor
   value.
5. The real installed settings match the repository settings after install.

## Confirmed decisions

- The requested repository main model is Opus.
- The repository no longer selects an advisor.
- The worker model remains unpinned.

## Open questions

None.
