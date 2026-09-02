Status: approved
Approved at: 2026-09-02T10:38:27+08:00
Approved from: 使用者同意將主模型與最高複雜度派工改為 `claude-fable-5-1`

# Fable model routing specification

## Observable behavior

1. `config/claude-settings.json` contains
   `model: claude-fable-5-1` and
   `crossSessionInbound: accept`, without a repository-managed advisor or
   worker-model environment override.
2. `CLAUDE.md` contains the canonical model-routing policy:
   - delegate every fragmentary task through Straw Boss or a subagent;
   - use Straw Boss for work that needs a managed app workroom and a subagent
     for self-contained fragments;
   - select `claude-fable-5-1` for the most complex delegated work;
   - select `sonnet` for pure code-writing work;
   - otherwise retain the configured `claude-fable-5-1` default.
3. `CLAUDE.md` directs Claude to repair Straw Boss in
   `~/projects/straw-boss`, bump and push the plugin, run
   `herdr reload plugin`, and resume the original task when Straw Boss itself
   causes friction.
4. A fresh or upgrade install writes the `claude-fable-5-1` main setting
   and installs the updated root prompt while preserving unrelated user
   settings.
5. Current installer help and README describe the exact main model and the
   routing authority accurately.

## Edge cases

- A small task that needs the target app's real harness or durable workroom
  uses Straw Boss; a self-contained fragment may use a subagent.
- A task that includes design, investigation, coordination, or verification is
  not classified as pure code writing merely because it also changes code.
- `claude-fable-5-1` serves both as the main model and the explicit
  highest-complexity delegated model; ordinary work inherits it.
- Straw Boss source delivery runs only when Straw Boss itself causes the
  friction, not for an application defect or an operator mistake.
- Historical specifications remain unchanged as records of earlier behavior.

## Compatibility constraints

- Preserve `crossSessionInbound=accept`, hook/status-line merge behavior, Codex
  role models, and exact-value uninstall cleanup.
- Preserve current routing ownership and the distinction between managed-app
  workrooms and self-contained subagents.
- Preserve the exact `claude-fable-5-1` model string selected by the user;
  Fable 5.1 supplies a 1M context window by default.

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
  currently manages `opus[1m]` main and `crossSessionInbound=accept`.
- [`CLAUDE.md`](../../../CLAUDE.md) already owns routing and delegation policy.
- [`tests/install.sh`](../../../tests/install.sh),
  [`tests/uninstall.sh`](../../../tests/uninstall.sh), and
  [`tests/prompts.sh`](../../../tests/prompts.sh) are the relevant executable
  seams.

## Reality anchor and checkpoint

Reality anchor: testing.

Checkpoint: focused prompt and installer assertions first fail against the
current Opus policy, then all installer, uninstall, prompt, syntax, JSON, and
diff checks pass; after `bash scripts/install.sh`, the real
`~/.claude/settings.json` and `~/.claude/CLAUDE.md` expose the approved values
and routing text, and Claude Code accepts the exact configured model string.
