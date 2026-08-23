# Codex Desktop WSL installer design

## Approach

Add a standalone `scripts/install-codex-desktop-wsl.sh` rather than extending the
Linux-home installer. The script resolves a Windows home path, then installs
repository-managed entries as ordinary copies under Windows `.codex`.

## Interfaces and data flow

1. Repository files are the source.
2. Windows home is supplied by `--windows-home` or discovered with
   `cmd.exe` plus `wslpath`.
3. Each managed file or top-level directory entry is compared with its target.
4. Missing entries are copied; equal entries are accepted; conflicts fail or
   move to a timestamped backup when `--force` is set.

Managed entries are `AGENTS.md`, each custom `skills/*` directory, each
`codex/agents/*.toml`, each `codex/rules/*.rules`, `codex/hooks.json`, and each
`codex/hooks/*.sh`.

## Precedent

`scripts/install.sh` supplies the repository's argument handling, conflict,
backup, logging, and managed-surface conventions. The Desktop installer uses
copies because Linux symlinks are not a dependable Windows application
interface.

## Decisions and risks

- Per-entry copying preserves Windows `.system` skills and unrelated plugins.
- `config.toml` and runtime state stay machine-local.
- Installation is snapshot synchronization, not live sync; users rerun the
  script after repository updates.
- Forced replacement is recoverable through a timestamped Windows-local backup.

## Correctness seam

`tests/install_codex_desktop_wsl.sh` calls the public script with a temporary
Windows-home-shaped directory and verifies install, idempotence, refusal,
backup, and unrelated-content preservation. The focused test must fail before
the implementation exists and pass afterward.

No separate human appropriateness decision is required.
