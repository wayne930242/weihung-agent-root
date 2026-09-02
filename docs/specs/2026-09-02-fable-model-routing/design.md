# Fable model routing design

## Chosen approach

- Change the managed Claude setting from `opus[1m]` to
  `claude-fable-5-1` while retaining `crossSessionInbound=accept`.
- Add one `Model Work Routing` section to `CLAUDE.md` before the existing
  delegation mechanics. It classifies work once and supplies the model choice
  to Straw Boss or a subagent without duplicating that policy elsewhere.
- Keep existing app/workroom routing intact: Straw Boss owns managed-app work
  and durable coordination; a native subagent owns self-contained fragments.
- Add the user-authorized Straw Boss repair lifecycle to the same canonical
  section because it is part of delegation behavior.
- Update current installer help, README, prompt assertions, and installer
  expectations. Historical approved specs remain unchanged.

## Interfaces and data flow

`config/claude-settings.json` is merged into `~/.claude/settings.json` by
`scripts/install.sh`. The merge replaces the managed `model` value with
`fable`; no additional migration is needed because model replacement is an
existing overlay behavior.

`CLAUDE.md` is symlinked to `~/.claude/CLAUDE.md`, so the canonical policy is
installed directly. Delegation reads that policy, selects the work route, and
passes an explicit model only for the two exceptional classes:

- highest complexity: `claude-fable-5-1`;
- pure code writing: `sonnet`.

All other work inherits the configured `claude-fable-5-1` main model.

## Existing precedent

- `CLAUDE.md` already owns Routing, Complex Delegation, and Direct Cross-Model
  Consult rules.
- `config/claude-settings.json` already owns the main Claude model.
- `tests/prompts.sh` checks installed prompt policy; `tests/install.sh` checks
  managed settings through a fake home.
- `scripts/uninstall.sh` removes managed settings by exact current value, so
  changing the fragment automatically keeps uninstall value-sensitive.

## Decisions and trade-offs

- Keep `claude-fable-5-1` exact for both the main session and the
  highest-complexity route. Fable 5.1 provides its 1M context window by
  default, so a context suffix is unnecessary.
- Describe task classes by observable work content. A task with design,
  investigation, coordination, or verification is not pure code writing.
- Trigger Straw Boss source delivery only when Straw Boss itself causes the
  friction. This keeps application defects in their owning repositories.

## Risks

- Similar delegation prose in several sections could conflict. One canonical
  section supplies model choice; existing sections keep transport mechanics.
- A broad code-writing label could route mixed engineering work to Sonnet. The
  prompt explicitly limits it to tasks consisting only of code writing.
- Source settings can pass while the user root stays stale. Verification runs
  the real installer and inspects the installed model and prompt.

## Correctness method

First update focused prompt and installer assertions and prove they fail
against the current Opus policy. Then update settings, prompt, installer help,
and README. Run full prompt, install, and uninstall suites; shell syntax, JSON,
and diff checks; execute the real installer; and inspect the installed model
and canonical routing text.
