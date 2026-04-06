# Codex Assets

This directory contains Codex-specific assets for the user-level install surface.

- `agents/` contains lightweight custom subagents in TOML.
- `rules/` contains approval policy rules.
- `hooks/` contains optional hook scripts.
- `hooks.json` wires the hook scripts to Codex events.

The installer places these files under `~/.codex/` but intentionally does not rewrite `~/.codex/config.toml` in the light layout.
