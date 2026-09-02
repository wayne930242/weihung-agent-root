# Fable model routing requirements

## Outcome and actors

Claude Code users installing this repository receive Fable as the main model
and one canonical model-routing policy in `CLAUDE.md` for delegated work.

## In scope

- Set the repository-managed Claude main model to
  `claude-fable-5-1`.
- Make `CLAUDE.md` the authority for Claude model division.
- Delegate every fragmentary task through Straw Boss or a subagent.
- Route the most complex delegated work to `claude-fable-5-1`.
- Route pure code-writing work to `sonnet`.
- Direct Claude to repair Straw Boss in `~/projects/straw-boss`, bump and push
  the plugin, then run `herdr reload plugin` when Straw Boss itself causes
  friction.
- Update installer behavior, current documentation, and executable tests.
- Install the result into the real Claude user root and verify source and
  installed state separately.

## Out of scope

- Changing Codex role models.
- Rewriting historical specs that accurately record earlier model policies.
- Changing `~/projects/straw-boss` when no real Straw Boss defect is being
  handled.
- Committing or pushing this repository.

## Scenarios

1. A fresh install writes `model=claude-fable-5-1` and preserves
   `crossSessionInbound=accept`.
2. A fragmentary task is delegated through Straw Boss when it needs a managed
   app workroom, or through a subagent when it is self-contained.
3. The most complex delegated work explicitly selects
   `claude-fable-5-1`.
4. A delegated task consisting only of code writing explicitly selects
   `sonnet`.
5. Other work keeps the configured `claude-fable-5-1` default instead of
   being forced to Sonnet.
6. When Straw Boss itself causes friction, Claude repairs its source repo,
   bumps and pushes the plugin, reloads it through Herdr, and then resumes the
   original task.
7. The real installed settings and root prompt match the repository after
   installation.

## Confirmed decisions

- The main model setting is `claude-fable-5-1`.
- Only the most complex delegated work selects `claude-fable-5-1`.
- Pure code-writing work selects `sonnet`.
- `CLAUDE.md` owns the model-routing policy.

## Open questions

None.
