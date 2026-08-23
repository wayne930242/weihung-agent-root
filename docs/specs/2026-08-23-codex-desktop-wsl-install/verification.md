# Codex Desktop WSL installer verification

## Requirement-to-evidence mapping

- Shared global guidance: repository `AGENTS.md` now contains Windows/WSL path
  interoperability rules; `cmp` confirms the Windows installed copy matches.
- Managed Codex surface: the real install copied guidance, custom skills,
  agents, rules, hooks configuration, and hook scripts into Windows `.codex`.
- Preserve Windows-local state: inspection confirms `.system` skills and
  `config.toml` remain present; the installer does not target plugins,
  authentication, history, databases, or runtime state.
- Safe conflicts: the focused integration test proves refusal without
  `--force` and preservation through timestamped backup with `--force`.
- Repeatability: a second real install completed with every entry reported
  `OK`.

## Automated results

- Red: `tests/install_codex_desktop_wsl.sh` failed because the public installer
  did not yet exist.
- Green: `tests/install_codex_desktop_wsl.sh` passed after implementation.
- Existing suites passed: `tests/install.sh`, `tests/uninstall.sh`,
  `tests/hooks.sh`, `tests/codex_hooks.sh`, and `tests/bootstrap.sh`.
- Static checks passed: `bash -n` and `git diff --check`.
- `shellcheck` was unavailable and therefore skipped.

## Operational evidence

- Real command: `bash scripts/install-codex-desktop-wsl.sh --force`.
- Backup created under Windows Local AppData for the previous `AGENTS.md` and
  `hooks.json`.
- A subsequent real run without `--force` was idempotent.

## Deviations and gaps

- The first real discovery run emitted a harmless `cmd.exe` UNC working-directory
  warning. Discovery was changed to invoke Windows interop from `/mnt/c`; the
  warning did not recur.
- WSL emits an existing `/etc/fstab` mount warning before commands. It is outside
  this change and did not affect installation or tests.
- No commit, push, CI, deployment, or browser verification was requested or
  performed.
