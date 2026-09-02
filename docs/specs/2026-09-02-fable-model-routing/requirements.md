# Claude model routing requirements

## Outcome and actors

Claude Code users installing this repository receive Opus 1M as the default
main model and one canonical work-routing policy in `CLAUDE.md`.

## In scope

- Set the repository-managed Claude main model to
  `opus[1m]`.
- Make `CLAUDE.md` the authority for Claude model division.
- Carry simple work from a direct user instruction without delegation.
- Delegate other fragmentary tasks through Straw Boss or a subagent.
- Route the most complex delegated work with the orchestrator's current model.
- Otherwise, route document-writing work to `codex`.
- Otherwise, route code-writing, investigation, and lookup work to `sonnet`.
- Define an `Orchestrator 權限移交` flow for Opus to recommend Fable 5.1 when
  it judges work to have extreme complexity.
- Require explicit user approval before creating an independent Herdr pane,
  running Fable 5.1 through `boss-say` there, and closing the original pane.
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

1. A fresh install writes `model=opus[1m]` and preserves
   `crossSessionInbound=accept`.
2. Simple work requested directly by the user is completed by the main agent
   without delegation.
3. Other fragmentary work is delegated through Straw Boss when it needs a
   managed app workroom, or through a subagent when it is self-contained.
4. The most complex delegated work inherits the orchestrator's current model,
   whether it is the Opus 1M default or a model selected for the current work.
5. Unless the highest-complexity rule applies, document-writing work is
   delegated to `codex`.
6. Unless either preceding rule applies, code-writing, investigation, and
   lookup work explicitly selects `sonnet`.
7. Other work keeps the orchestrator's current model instead of being forced
   to Sonnet.
8. When Straw Boss itself causes friction, Claude repairs its source repo,
   bumps and pushes the plugin, reloads it through Herdr, and then resumes the
   original task.
9. When an Opus orchestrator judges work to have extreme complexity, it
   recommends an `Orchestrator 權限移交` to Fable 5.1 and waits for explicit
   user approval.
10. After approval, it opens an independent Herdr pane, invokes Straw Boss
    `boss-say` there with `claude-fable-5-1`, and closes the original pane only
    after `boss-say` is running in the new pane.
11. The real installed settings and root prompt match the repository after
   installation.

## Confirmed decisions

- The default main model setting is `opus[1m]`.
- A direct user instruction for simple work is executed without delegation.
- The highest-complexity route takes precedence and inherits the orchestrator's
  current model, allowing a user-selected Opus 1M or Fable 5.1 session.
- Otherwise, document-writing work is delegated to `codex`.
- Otherwise, code-writing, investigation, and lookup work selects `sonnet`.
- The extreme-complexity escalation is named `Orchestrator 權限移交` and is
  gated by explicit user approval.
- An approved handoff uses a new independent Herdr pane, runs `boss-say` there
  with `claude-fable-5-1`, then closes the original orchestrator pane.
- `CLAUDE.md` owns the model-routing policy.

## Open questions

None.
