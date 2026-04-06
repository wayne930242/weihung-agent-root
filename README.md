# weihung-user-claude

Personal user-root light agent system for Claude Code and Codex.

The repo keeps global behavior in version control, but deliberately separates:

- shared working agreements
- Claude-specific prompt, agents, and hooks
- Codex-specific prompt, subagents, rules, and hooks

The goal is to keep the user-root layer thin and stable, while leaving personal machine config such as credentials, MCP servers, model choices, and trusted project state under direct user control.

## Design

This repo follows a light split:

- `shared/`: cross-product principles that are stable across tools
- `claude/`: assets that only make sense for Claude Code
- `codex/`: assets that only make sense for Codex

That split matters because the products do not expose the same primitives:

- Claude uses `CLAUDE.md`, `~/.claude/settings.json`, and Markdown subagents
- Codex uses `AGENTS.md`, `rules/*.rules`, `hooks.json`, and TOML subagents

Trying to force both products through one identical file model creates unnecessary coupling.

## Layout

```text
CLAUDE.md                          # thin Claude root prompt, imports shared fragments
AGENTS.md                          # thin Codex root prompt
shared/
  communication.md
  engineering.md
  context-management.md
claude/
  agents/
    security-reviewer.md
    silent-failure-hunter.md
  hooks/
    log-notification.sh
    log-stop.sh
codex/
  agents/
    docs-researcher.toml
    safety-reviewer.toml
  rules/
    default.rules
  hooks/
    log-session-start.sh
    log-stop.sh
  hooks.json
rules/
  clean-architecture.md
  go.md
  typescript.md
  python.md
  shell.md
  markdown.md
  deployment.md
  chinese-writing.md
skills/
  leveraging-tasks/
  providing-knowledge/
  investigating/
  inspecting/
  reflecting-to-root/
scripts/
  install.sh
  uninstall.sh
  bootstrap.sh
config/
  claude-hooks.json
  codex-config.toml                # optional snippet, not auto-merged
```

## Install

Install into your real user root:

```bash
bash scripts/install.sh
```

Bootstrap a new machine by cloning or updating the repo into the standard location and then running the installer:

```bash
bash scripts/bootstrap.sh
```

Remote one-liner bootstrap:

```bash
curl -fsSL https://raw.githubusercontent.com/wayne930242/weihung-user-claude/main/scripts/bootstrap.sh | bash
```

Smoke test against a fake home first:

```bash
bash scripts/install.sh --home /tmp/weihung-user-claude-smoke
```

Replace conflicting managed targets only when you mean it:

```bash
bash scripts/install.sh --force
```

Forward installer flags through bootstrap the same way:

```bash
bash scripts/bootstrap.sh --force
```

Uninstall managed assets and restore from the latest backup when available:

```bash
bash scripts/uninstall.sh
```

## Managed Surface

The installer manages only these user-root surfaces.

### Claude

- `~/.claude/CLAUDE.md`
- `~/.claude/shared/*.md`
- `~/.claude/agents/*.md`
- `~/.claude/hooks/*.sh`
- merge into `~/.claude/settings.json` using `config/claude-hooks.json`

### Codex

- `~/.codex/AGENTS.md`
- `~/.codex/agents/*.toml`
- `~/.codex/rules/*.rules`
- `~/.codex/hooks/*.sh`
- `~/.codex/hooks.json`

## Intentionally Not Managed

These remain user-controlled on purpose:

- `~/.claude/settings.local.json`
- `~/.codex/config.toml`
- credentials and auth
- MCP server definitions
- plugin enablement
- personal model preferences
- trust and approval state

This is especially important for Codex. `config.toml` often carries machine-local trust, MCP, plugin, and feature flags that should not be overwritten by a global prompt repo.

## Conflict And Backup Behavior

- Default behavior is fail-fast. If a managed target already exists, installation stops.
- `--force` moves conflicting files into `~/.local/state/weihung-user-claude/backups/<timestamp>/` before replacing them.
- Claude `settings.json` is merged, not symlinked, so existing non-hook settings remain intact.
- Codex `config.toml` is left untouched in the light layout.

## Uninstall Behavior

- `scripts/uninstall.sh` looks for the latest backup under `~/.local/state/weihung-user-claude/backups/`.
- If a backup exists for a managed path, that file is restored.
- If no backup exists for a managed path, the managed symlink is removed.
- Managed Claude hooks are removed from `~/.claude/settings.json`.
- `~/.codex/config.toml` is still left untouched, because it is not installer-managed.

## Claude Notes

Claude supports user memory and imports, so the Claude side is intentionally thin:

- `CLAUDE.md` holds routing and Claude-only behavior
- `@shared/...` imports pull in stable cross-product guidance
- hooks are wired through `settings.json`, because that is Claude's official hook surface

Current Claude hooks are deliberately minimal:

- `Notification` logs to `~/.claude/state/weihung-user-claude/hooks.jsonl`
- `Stop` logs to the same file

## Codex Notes

Codex now has first-class support for:

- global and project `AGENTS.md`
- `rules/*.rules`
- `hooks.json`
- custom subagents in `agents/*.toml`

This repo uses that split directly:

- `AGENTS.md` stays focused on general working agreements
- `codex/rules/default.rules` handles approval policy
- `codex/hooks.json` and `codex/hooks/*.sh` handle automation
- `codex/agents/*.toml` handle specialized delegation

Codex hooks are still better treated as optional infrastructure, not mandatory base config. The installer places the files, but does **not** auto-enable the experimental hook feature in `~/.codex/config.toml`.

If you want to opt in manually, copy the relevant snippet from:

- `config/codex-config.toml`

## Why This Is Light

- The global prompt files are short.
- Approval policy is not mixed into prompt prose.
- Automation is not mixed into prompt prose.
- Product-specific capabilities live in product-specific directories.
- The installer does not silently take over the full home config surface.

## Verification

The repo currently verifies:

- installer behavior with `tests/install.sh`
- Claude hook scripts with `tests/hooks.sh`
- Codex hook scripts with `tests/codex_hooks.sh`
- bootstrap clone/update behavior with `tests/bootstrap.sh`
- uninstall restore/remove behavior with `tests/uninstall.sh`

## Not Tracked

- personal values in `settings.json` / `settings.local.json`
- generated state such as `todos/`, `projects/`, `statsig/`
- machine-specific additions outside the managed surfaces above
