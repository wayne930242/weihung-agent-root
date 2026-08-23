# Codex Desktop WSL installer specification

## Observable behavior

- `bash scripts/install-codex-desktop-wsl.sh` discovers the current Windows
  profile through Windows interop and targets its `.codex` directory.
- `--windows-home PATH` overrides discovery for testing or nonstandard setups.
- Existing matching files are reported as already installed.
- Existing differing files or directories stop installation without mutation.
- `--force` moves differing targets into a timestamped backup tree under the
  Windows user's local application data before installing repository copies.
- The script never removes unrelated Windows `.codex` content.

## Compatibility and edge cases

- Paths containing spaces are quoted throughout.
- The script fails with an actionable message when Windows interop or path
  conversion is unavailable.
- Repository directories are copied by managed entry, not mirrored with a
  deletion-capable operation.
- `config.toml`, auth, plugins, `.system` skills, logs, and databases remain
  untouched.

## Non-goals

- Live bidirectional synchronization.
- Cross-platform sharing of mutable runtime state.

## Applied standards

- `AGENTS.md`: read-before-write, scoped changes, verification, Traditional
  Chinese communication, and no unrelated cleanup.
- `rules/shell.md`: shell script safety and quoting.
- [OpenAI AGENTS.md documentation](https://learn.chatgpt.com/docs/agent-configuration/agents-md):
  Windows Codex Desktop must receive global guidance in its own Codex home.

## Correctness strategy

- Add a shell integration test using a temporary Windows-home-shaped directory.
- Verify first install, idempotent rerun, conflict refusal, forced backup, and
  preservation of unrelated content.
- Run the new test plus the existing installer test suite.
- Execute the script once against the real Windows Codex home with `--force`,
  then inspect installed content without altering the existing
  `codex/hooks.json` working-tree change.

## User confirmation

Confirmed by the user's 2026-08-23 request to make Codex Desktop consume the
Linux-root Codex agent system and add a WSL installation script to this
repository.
