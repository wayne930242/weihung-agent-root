# Codex Assets

This directory contains Codex-specific assets for the user-level install surface.

- `agents/` contains lightweight custom subagents in TOML.
- `rules/` contains the managed approval policy; Codex keeps its own `default.rules`.
- `hooks/` contains hook scripts.
- `hooks.json` wires the hook scripts to Codex events.

The installer places these files under `~/.codex/` and links the repository skills into `~/.agents/skills/`.
It changes only the keys of `config/codex-managed.toml` inside `~/.codex/config.toml`.
