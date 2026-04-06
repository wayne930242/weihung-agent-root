# weihung-user-claude

Personal user-root prompt system for Claude Code and Codex.
This repo is meant to be the source of truth for global prompt files, shared rules, selected agents, and Claude hook scripts, then installed into `~/.claude/` and `~/.codex/`.

## Goal

Keep global AI behavior in version control without taking over the entire home-directory config surface.

This repo manages:

- Claude global system prompt
- Codex global system prompt
- reusable agent markdown files
- shared rules and skills
- Claude hook scripts plus their managed hook config fragment

This repo intentionally does **not** manage:

- secrets or credentials
- personal model selection
- MCP server definitions
- plugin enablement
- `~/.codex/config.toml`
- `~/.claude/settings.local.json`

## Layout

```text
CLAUDE.md                          # Claude Code global system prompt
AGENTS.md                          # Codex global system prompt
rules/
  clean-architecture.md
  go.md
  typescript.md
  python.md
  shell.md
  markdown.md
  deployment.md
  chinese-writing.md
agents/
  silent-failure-hunter.md
  security-reviewer.md
hooks/
  log-notification.sh              # Claude Notification hook target
  log-stop.sh                      # Claude Stop hook target
skills/
  leveraging-tasks/
  providing-knowledge/
  investigating/
  inspecting/
  reflecting-to-root/
scripts/
  install.sh                       # user-root installer
config/
  claude-hooks.json                # hook fragment merged into ~/.claude/settings.json
```

## Install

Install into your real user root:

```bash
bash scripts/install.sh
```

Smoke test against a fake home directory first:

```bash
bash scripts/install.sh --home /tmp/weihung-user-claude-smoke
```

Force replacement when a managed target already exists:

```bash
bash scripts/install.sh --force
```

## What The Installer Changes

The installer creates these symlinks:

- `~/.claude/CLAUDE.md` -> repo `CLAUDE.md`
- `~/.claude/agents/*.md` -> repo `agents/*.md`
- `~/.claude/hooks` -> repo `hooks/`
- `~/.codex/AGENTS.md` -> repo `AGENTS.md`

The installer also merges the repo-managed Claude hook fragment into:

- `~/.claude/settings.json`

Existing keys in `~/.claude/settings.json` are preserved. Only the repo `hooks` payload is merged in.

## Conflict And Backup Behavior

- Default behavior is fail-fast. If a managed target already exists, installation stops.
- `--force` moves conflicting files into `~/.local/state/weihung-user-claude/backups/<timestamp>/` before replacing them.
- `settings.json` is merged, not symlinked, so local non-hook settings stay under user control.

## Claude Hooks

Claude hooks are configured through `~/.claude/settings.json`, not through `CLAUDE.md`.

This repo keeps hook logic split into two parts:

- `hooks/*.sh`: the executable scripts
- `config/claude-hooks.json`: the managed settings fragment that points Claude to those scripts

Current hooks are intentionally minimal and safe:

- `Notification` appends a JSONL record to `~/.claude/state/weihung-user-claude/hooks.jsonl`
- `Stop` appends a JSONL record to the same file

The point of this first version is reliable installation and traceability, not aggressive workflow automation.

## Routing Model

`CLAUDE.md` contains the routing table. At a high level:

1. If an external or built-in skill already fits, use it directly.
2. Development work routes through `leveraging-tasks`.
3. Questions route through `providing-knowledge`.
4. Research routes through `investigating`.
5. Audits and checks route through `inspecting`.

## Skills

### leveraging-tasks

Thin router for development work. It keeps implementation, design, debugging, and deployment distinct while still allowing refactor pressure to surface early.

### providing-knowledge

Answers questions by building a mental model first. The emphasis is clarity, directness, and honest uncertainty.

### investigating

Handles research with traceable evidence. It separates confirmed facts from inference.

### inspecting

Builds a check plan first, then verifies each item systematically.

### reflecting-to-root

Routes session learnings to the correct scope:

- cross-project patterns belong in `~/.claude/`
- project-specific patterns belong in the project-local `.claude/`

## Design Principles

- `CLAUDE.md` is the constitution: short, global, and always loaded.
- `rules/` hold scoped laws that are cheaper than bloating the root prompt.
- `skills/` hold process leverage, not random snippets.
- the installer stays narrow on purpose; it should not silently take over personal machine config.

## Codex Scope

Codex support is intentionally narrower than Claude support in v1.

This repo provides:

- `AGENTS.md` as the global Codex prompt entrypoint

This repo does not currently provide:

- automated `~/.codex/config.toml` merge
- a Codex hook system
- plugin or MCP configuration management

That boundary is deliberate. `config.toml` usually carries local trust, model, plugin, and MCP decisions that should remain personal unless there is a strong reason to centralize them.

## Not Tracked

- `settings.json` / `settings.local.json` with personal values
- generated state such as `todos/`, `projects/`, `statsig/`
- machine-specific or legacy local additions outside this repo's managed surface
