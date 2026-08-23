# Codex Desktop WSL installer requirements

## Outcome and actors

A WSL user can install this repository's Codex agent system into the Windows
Codex Desktop home so Linux Codex and Codex Desktop use the same repository
guidance and managed assets.

## In scope

- Add the Windows/WSL path interoperability guidance to the shared `AGENTS.md`.
- Provide an idempotent WSL script that discovers the Windows user profile.
- Install the repository-managed Codex surface into Windows `~/.codex`:
  `AGENTS.md`, custom skills, agents, rules, `hooks.json`, and hook scripts.
- Preserve Windows-only `.system` skills, plugins, authentication, state, and
  `config.toml`.
- Back up conflicting Windows targets before replacement when explicitly forced.
- Document and test the installer.

## Out of scope

- Sharing mutable Codex runtime state, authentication, history, databases, or
  machine-local `config.toml` between Windows and WSL.
- Installing or modifying WSL itself.
- Editing the existing user change in `codex/hooks.json`.

## Scenarios

1. A normal install copies missing managed assets into Windows Codex home.
2. Re-running against matching installed content succeeds without changes.
3. A conflicting target fails safely unless `--force` is supplied.
4. Forced installation backs up the conflicting target, then installs the
   repository version.
5. Windows-only Codex assets remain untouched.

## Confirmed decisions

- The repository remains the source of truth.
- Windows receives copies rather than Linux symlinks because Windows Codex must
  be able to read the files independently of Linux symlink semantics.
- Machine-local Codex configuration and state are not shared.

## Open questions

- None.
