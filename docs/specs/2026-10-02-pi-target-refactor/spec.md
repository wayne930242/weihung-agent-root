Status: approved
Approved at: 2026-10-02
Approved from: 核准，開始做

# pi-target refactor: spec

Decisions: [decision.md](decision.md).

## Observable behavior

1. `bash scripts/install.sh` on a home that the current version installed writes the same files with the same content as before the refactor: `~/.pi/agent/settings.json`, `mcp-adapter.json`, `AGENTS.md`, `herdr-agents/config.json`, tier roles, `~/.pi-lens/config.json`, `open-tui.json`, ported resources, and the marker.
2. `bash scripts/install.sh` on an empty home produces the same files as before the refactor.
3. `bash scripts/uninstall.sh` after either install restores the home to its pre-install content, including on a marker written by the current, pre-refactor version.
4. `python3 scripts/pi-target.py <migrate|install|uninstall|apply-profile>` keeps its arguments and exit behavior. `migrate` still validates `PI_HERDR_AGENTS_ROOT` before any file changes; it no longer renames weihung-user-claude paths.
5. `python3 scripts/pi-pins.py <outdated|bump|auto|schedule|unschedule>` keeps its behavior and finds every pin it finds today.
6. Bumping a git pin still removes the previous revision of that package from `settings.json`.

## Edge cases

- A marker that still holds keys only the removed migrations wrote (for example `retired_packages: ["npm:pi-claude-bridge"]`): uninstall restores them as before; install leaves them in place.
- A failed install midway, then rerun or uninstall: behaves as today (`tests/pi_review_fixes.py` cases for retry and backups keep passing in their new home).
- `--skip-external`, `--force`, `--home`: unchanged.

## Compatibility and non-goals

- The marker JSON keys and meanings stay the same; no state migration.
- No change to installed packages, pins, settings values, or generated text.
- No new dependencies; standard library only, as today.
- Not a goal: changing `install.sh` / `uninstall.sh`, the pi package in `pi/extensions/`, or how strategies are defined.

## Applied standards

- [rules/clean-architecture.md](../../../rules/clean-architecture.md): split the god module; one responsibility per module; config at the edges (pins and paths in one module).
- [rules/python.md](../../../rules/python.md): type hints with return types, `pathlib`, `ValueError` for validation. New and moved functions get type hints.
- Repository `AGENTS.md`: installers never overwrite user files silently; run the covering tests before each commit; exercise installer changes with `--home` on a temporary directory before the real home.

## Reality anchor

- **Golden check**, added first and run after every phase: build fixture homes in a temporary directory (empty home; home with this machine's current settings, marker, and `mcp-adapter.json`, with credentials stripped), run install then uninstall with `--skip-external`, and compare every produced file against snapshots recorded from the pre-refactor code. Snapshots are recorded once before phase 0; only phase 0's intended removals may change them, reviewed by hand.
- **Existing suites** after every phase: `bash tests/install.sh`, `bash tests/uninstall.sh`, every `python3 tests/*.py`, every `node --experimental-strip-types --test tests/*.mjs`.
- **Real home checkpoint** at the end: `bash scripts/install.sh` on this machine, then confirm `settings.json`, `mcp-adapter.json`, `AGENTS.md`, and the marker are byte-identical to before, and pi starts.
