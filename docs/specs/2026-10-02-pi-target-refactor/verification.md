# pi-target refactor: verification

Spec: [spec.md](spec.md). Commits: `f2dcbb7` (phase 0), `2f2f8e8` (phase 1), `6e8813a` (phase 2).

## Requirements

| Requirement | Evidence | Result |
|---|---|---|
| 1. Reinstalling a home the current version installed writes the same files | Golden check (`scratch/golden.py`, base `e2ec92d`) on a copy of this machine's managed files and marker: identical after install, after every phase. Real home: `bash scripts/install.sh` with external installs, then `cmp` against copies taken before: `settings.json`, `mcp-adapter.json`, `AGENTS.md`, the marker, `herdr-agents/config.json`, `open-tui.json`, `~/.pi-lens/config.json`, and every tier role identical. | pass |
| 2. Installing into an empty home produces the same files (`--skip-external`) | Golden check, empty fixture: 16 files identical after install, after every phase. | pass |
| 2. Installing into an empty home produces the same files (external installs) | `tests/pi_fresh_machine.py` and `tests/pi_port_install.py` run the external path with fake pi and npm and pass; their output was not byte-compared with the base. | unknown |
| 3. Uninstall restores the pre-install content, including on a marker the pre-refactor version wrote | Golden check: all three fixtures identical after uninstall, the real-home fixture using this machine's pre-refactor marker (which lacks `previous_settings_present`). `tests/pi_steps.py`, `tests/install.sh`, `tests/uninstall.sh` pass. | pass |
| 4. `pi-target.py` keeps its actions; `migrate` validates `PI_HERDR_AGENTS_ROOT` before changes and no longer renames | `tests/pi_herdr_agents_root.py` passes; `tests/install.sh` runs `apply-profile`; the rename code and its test are gone (`f2dcbb7`). | pass |
| 5. `pi-pins.py` keeps its behavior and finds every pin | `tests/pi_pins.py` passes; `python3.14 scripts/pi-pins.py outdated` with the launchd interpreter lists 24 pins, as before. | pass |
| 6. Bumping a git pin still retires its previous revision | `tests/pi_packages.py` (`test_previous_git_bridge_revision_is_restored`, `test_earlier_straw_boss_revisions_are_retired_for_the_pin`, `test_external_git_switch_keeps_the_new_checkout`) and the golden synthetic fixture's old bridge revision. | pass |
| Edge: a marker holding keys only removed migrations wrote | This machine's marker holds `retired_packages: ["npm:pi-claude-bridge"]`; golden real fixture install and uninstall identical to base. | pass |
| Edge: failed install, then rerun or uninstall | `tests/pi_steps.py` (`test_failed_external_install_can_retry_and_uninstall`, `test_instructions_backup_survives_a_failed_install_and_uninstall`), `tests/pi_resources.py`. | pass |
| Uninstall runs restores in reverse install order | `tests/pi_steps.py` `test_uninstall_restores_the_steps_in_reverse_install_order`. | pass |
| Type hints on new and moved functions | `npx pyright scripts/pi-target.py scripts/pi_root tests/...`: 0 errors; `ruff check`: clean. | pass |

Suites after phase 2: every `python3 tests/*.py` (11 files), `bash tests/install.sh`, `bash tests/uninstall.sh`, `node --experimental-strip-types --test tests/*.mjs` (3) pass.
pi starts on the reinstalled home: `pi --mode rpc --no-session --offline` answered `get_commands` with 162 commands.

## Deviations

- Spec decision "delete the `previous_*_present` fallback" was reversed before implementation: this machine's marker has neither present list, so its uninstall needs the fallback. Recorded in [decision.md](decision.md).
- The upstream `elidickinson/pi-claude-bridge` prefix was added to the removed migrations, the same kind as the fork prefixes listed.
- The design's separate resources step became part of the package step, because the external calls depend on each other's order; [design.md](design.md) records the reason.
- `pyrightconfig.json` was added (`extraPaths: scripts, tests`) so type checks resolve `pi_root` and `support`.

## Gaps

- Not byte-compared: a fresh install with external installs (requirement 2). Phase 2 saves the marker after every step, so a fresh external install may order marker keys differently from the base; file content and behavior are covered by the fake-pi suites.
- The lens Pyright server still reports `pi_root` imports as unresolved because it started before `pyrightconfig.json` existed; the two reports seen are marked false-positive, and `npx pyright` is clean.
- Not pushed at the time of writing.

## Reflexive

- macOS `/var` vs `/private/var` in golden paths: gap; no change, specific to this refactor-time script.
- `git checkout <file>` blocked by CC Safety Net: gap; no change, the same class of Safety Net quirk is already in memory.
- Locals shadowing modules after the split: gap; no change, a one-time hazard of mechanical moves that pyright and an AST scan caught.
- lens Pyright server keeps its startup config: misdirection of "use `lens_diagnostics` for type checks after edits"; recorded as a tool-quirk memory (confirm with `npx pyright` after changing `pyrightconfig.json`) instead of a rule change, since it bites only when the configuration changes mid-session.
- ruff sorts `pi_root` before `support`: gap; no change, each test file sets the path itself.
