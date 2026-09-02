# Claude model routing design

## Chosen approach

- Change the managed Claude setting from `claude-fable-5-1` to `opus[1m]`
  while retaining `crossSessionInbound=accept`.
- Add one `Model Work Routing` section to `CLAUDE.md` before the existing
  delegation mechanics. It classifies work once and supplies the model choice
  to Straw Boss or a subagent without duplicating that policy elsewhere.
- Give a direct user instruction for simple work an explicit inline route
  before the delegation branches.
- Keep existing app/workroom routing intact: Straw Boss owns managed-app work
  and durable coordination; a native subagent owns self-contained fragments.
- Add the user-authorized Straw Boss repair lifecycle to the same canonical
  section because it is part of delegation behavior.
- Add a distinct `Orchestrator 權限移交` section for the approval-gated,
  terminal transfer from an Opus orchestrator to a Fable 5.1 `boss-say` pane.
- Update current installer help, README, prompt assertions, and installer
  expectations. Historical approved specs remain unchanged.

## Interfaces and data flow

`config/claude-settings.json` is merged into `~/.claude/settings.json` by
`scripts/install.sh`. The merge replaces the managed `model` value with
`opus[1m]`; no additional migration is needed because model replacement is an
existing overlay behavior.

`CLAUDE.md` is symlinked to `~/.claude/CLAUDE.md`, so the canonical policy is
installed directly. A simple task directly instructed by the user stays with
the main agent. Other fragmentary work enters delegation, which applies these
routes in order:

- highest complexity: the orchestrator's current model;
- otherwise, document writing: `codex`;
- otherwise, code writing, investigation, or lookup: `sonnet`.

All other work inherits the orchestrator's current model.

The authority-handoff data flow is linear: Opus judges extreme complexity,
recommends Fable 5.1, waits for explicit user approval, opens a new independent
Herdr pane, invokes `boss-say` there with `claude-fable-5-1`, and closes the
original pane after the new `boss-say` is running. Approval changes precedence:
the handoff replaces the normal current-model route for that work.

## Existing precedent

- `CLAUDE.md` already owns Routing, Complex Delegation, and Direct Cross-Model
  Consult rules.
- `config/claude-settings.json` already owns the main Claude model.
- `tests/prompts.sh` checks installed prompt policy; `tests/install.sh` checks
  managed settings through a fake home.
- `scripts/uninstall.sh` removes managed settings by exact current value, so
  changing the fragment automatically keeps uninstall value-sensitive.

## Decisions and trade-offs

- Keep `opus[1m]` exact as the installed default while routing the most complex
  work by inheritance. This lets a user switch the orchestrator to Fable 5.1
  for selected work without changing the prompt.
- State route precedence explicitly so overlapping work has one owner: highest
  complexity first, document writing second, and Sonnet work types third.
- Treat both direct user instruction and simplicity as required for inline
  execution; either condition missing leaves the normal delegation route in
  force.
- Keep authority transfer separate from ordinary model routing. It is a
  user-gated lifecycle transition that ends the original orchestrator pane,
  rather than an automatic model selection.
- Trigger Straw Boss source delivery only when Straw Boss itself causes the
  friction. This keeps application defects in their owning repositories.

## Risks

- Similar delegation prose in several sections could conflict. One canonical
  section supplies model choice; existing sections keep transport mechanics.
- A direct but complex request could be mistaken for inline work. The prompt
  requires both directness and simplicity before bypassing delegation.
- A research-backed document can match both document-writing and investigation
  routes. The ordered policy sends it to Codex unless it is a
  highest-complexity task.
- Closing the original pane before the destination is running could abandon
  the task. The prompt makes a running destination `boss-say` the close gate.
- Source settings can pass while the user root stays stale. Verification runs
  the real installer and inspects the installed model and prompt.

## Correctness method

First update focused prompt and installer assertions and prove they fail
against the current Fable policy. Then update settings, prompt, installer help,
and README. Run full prompt, install, and uninstall suites; shell syntax, JSON,
and diff checks; execute the real installer; and inspect the installed model
and canonical routing text.
