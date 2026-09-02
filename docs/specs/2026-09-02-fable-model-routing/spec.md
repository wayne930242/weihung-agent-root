Status: approved
Approved at: 2026-09-02T10:55:57+08:00
Approved from: 使用者新增極高複雜度時經同意轉交 Fable 5.1 的獨立 Herdr pane 流程，並命名為「Orchestrator 權限移交」

# Claude model routing specification

## Observable behavior

1. `config/claude-settings.json` contains
   `model: opus[1m]` and
   `crossSessionInbound: accept`, without a repository-managed advisor or
   worker-model environment override.
2. `CLAUDE.md` contains the canonical model-routing policy:
   - carry simple work from a direct user instruction without delegation;
   - delegate other fragmentary tasks through Straw Boss or a subagent;
   - use Straw Boss for work that needs a managed app workroom and a subagent
     for self-contained fragments;
   - inherit the orchestrator's current model for the most complex delegated
     work;
   - otherwise delegate document-writing work to `codex`;
   - otherwise select `sonnet` for code-writing, investigation, and lookup
     work;
   - retain the orchestrator's current model for all remaining work.
3. `CLAUDE.md` directs Claude to repair Straw Boss in
   `~/projects/straw-boss`, bump and push the plugin, run
   `herdr reload plugin`, and resume the original task when Straw Boss itself
   causes friction.
4. `CLAUDE.md` defines `Orchestrator 權限移交`:
   - an Opus orchestrator that judges work to have extreme complexity
     recommends transferring authority to `claude-fable-5-1`;
   - it waits for the user's explicit approval before starting the transfer;
   - after approval, the handoff supersedes the normal current-model route for
     that work;
   - after approval, it opens an independent Herdr pane and invokes the Straw
     Boss `boss-say` skill there with `claude-fable-5-1`;
   - once `boss-say` is running in the new pane, it closes the original
     orchestrator pane.
5. A fresh or upgrade install writes the `opus[1m]` main setting
   and installs the updated root prompt while preserving unrelated user
   settings.
6. Current installer help and README describe the exact main model and the
   routing authority accurately.

## Edge cases

- Directness alone does not bypass delegation: the task must be both directly
  instructed by the user and simple.
- A small task that needs the target app's real harness or durable workroom
  is not simple for this rule and uses Straw Boss; another self-contained
  fragment may use a subagent.
- Apply model routes in their listed order. The highest-complexity route takes
  precedence over every work-type route, and document writing takes precedence
  when a non-highest-complexity task also includes investigation or lookup.
- The installed orchestrator default is `opus[1m]`; a user may switch the
  current orchestrator to Fable 5.1 for a particular body of work without
  rewriting the routing policy.
- `Orchestrator 權限移交` does not trigger when the current orchestrator is not
  Opus, when complexity is below extreme, or when the user has not approved.
- Until approval, the normal current-model route remains in force; after
  approval, the authority-handoff route takes precedence for that work.
- If the user declines, the original orchestrator pane remains active and no
  handoff pane is created.
- The original pane stays open until Fable 5.1 `boss-say` is running in the
  new independent pane.
- Straw Boss source delivery runs only when Straw Boss itself causes the
  friction, not for an application defect or an operator mistake.
- Historical specifications remain unchanged as records of earlier behavior.

## Compatibility constraints

- Preserve `crossSessionInbound=accept`, hook/status-line merge behavior, Codex
  role models, and exact-value uninstall cleanup.
- Preserve current routing ownership and the distinction between managed-app
  workrooms and self-contained subagents.
- Preserve the exact `opus[1m]` default model string selected by the user.

## Non-goals

- No current change to `~/projects/straw-boss` without a confirmed Straw Boss
  defect.
- No Codex model change.
- No commit, push, release, or hosted deployment for this repository.

## Applied standards

- [`AGENTS.md`](../../../AGENTS.md): Traditional Chinese communication, read
  before write, scoped changes, and relevant verification.
- [`skills/leveraging-tasks/SKILL.md`](../../../skills/leveraging-tasks/SKILL.md):
  durable lifecycle and per-requirement evidence.
- Existing installer tests remain the executable public seam for fresh,
  upgrade, preservation, and uninstall behavior.

## Evidence and precedent

- [`config/claude-settings.json`](../../../config/claude-settings.json)
  supplies the installer-managed main model and
  `crossSessionInbound=accept`.
- [`CLAUDE.md`](../../../CLAUDE.md) already owns routing and delegation policy.
- [`tests/install.sh`](../../../tests/install.sh),
  [`tests/uninstall.sh`](../../../tests/uninstall.sh), and
  [`tests/prompts.sh`](../../../tests/prompts.sh) are the relevant executable
  seams.

## Reality anchor and checkpoint

Reality anchor: testing.

Checkpoint: focused prompt and installer assertions first fail against the
current Fable policy, then all installer, uninstall, prompt, syntax, JSON, and
diff checks pass; after `bash scripts/install.sh`, the real
`~/.claude/settings.json` and `~/.claude/CLAUDE.md` expose the approved values
and routing text.
