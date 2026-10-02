# pi-target refactor: design

Spec: [spec.md](spec.md).

## Modules

`scripts/pi-target.py` keeps its path and CLI; it puts `scripts/` on `sys.path` and calls `pi_root.cli.main()`.
`scripts/pi_root/` holds the logic:

| Module | Holds | From today's `pi-target.py` |
|---|---|---|
| `pins.py` | every pinned source, `PACKAGES`, `PINNED_GIT` (current prefixes only), `HERDR_AGENTS_SOURCE`, `PLAYWRITER` | the constants block |
| `paths.py` | `ROOT`, `MARKER`, config paths, company plugin defaults, env-overridable roots | the constants block |
| `jsonfile.py` | `read_json`, `write_json` | same names |
| `context.py` | `Context`: the home, the marker state, the run's flags, and `save()` | the locals `install` and `uninstall` passed around |
| `managed.py` | the managed-key mechanism: record previous once, record installed, restore when unchanged | `remember_previous`, `restore_managed_keys`, and the inline restore loops in `uninstall` |
| `packages.py` | identity (`package_source`, `package_id`, `unique_packages`, `obsolete_pin`), owned and local package lists, `plan`, and the package step, which also installs pi, Playwriter, the Herdr integration, and the ported resources | package helpers and the package parts of `install` / `uninstall` |
| `external.py` | `run`, the seam tests replace, and `run_company_plugin` | same names |
| `profile.py` | strategy routing, candidates, enabled models, tier roles, the profile step | `routing` … `update_profile`, its restore in `uninstall` |
| `instructions.py` | generated `AGENTS.md`, its backup and restore | the instructions parts of `install`, `uninstall`, and `apply-profile` |
| `configs.py` | the small config steps: UI and terminal and panes, built-in MCP off, mcp-adapter, pi-lens, open-tui, compaction | `update_*` / `restore_*` pairs |
| `resources.py` | `managed_resource`, ported team-toon-tack and pi-skills resources, their restore | same names |
| `steps.py` | `Step`, the ordered step list, `install`, `uninstall`, and `apply_profile` | `install`, `uninstall`, the apply-profile branch of `main` |
| `cli.py` | argparse and the four actions | `main` |

`scripts/pi-pins.py` imports `pi_root.pins` and `pi_root.packages` and rewrites pins in `pi_root/pins.py` instead of `pi-target.py`.

## Step interface

```python
@dataclass
class Context:
    home: Path
    state: dict          # the marker
    skip_external: bool = False
    force: bool = False
    herdr_root: str | None = None
    first_install: bool = False
    gone_plugins: list[str] = []   # company plugins this machine no longer has

class Step(NamedTuple):
    name: str
    apply: Callable[[Context], None]
    restore: Callable[[Context], None]
```

`install` runs `packages.plan`, then `apply` in list order, saving the marker after each step.
`plan` records the package sources and pre-install packages without saving, so a first install that stops at the instructions step still leaves no marker.
`uninstall` runs `restore` in reverse list order, then deletes the marker.
The list is today's install order, so fresh-install files keep their key order: instructions, mcp-adapter, pi-lens, open-tui, profile, UI, compaction, packages.

The package step covers pi, Playwriter, the Herdr integration, every pi package, and the ported resources, because their external calls depend on each other's order (resources install between aaaav and this repository's package; uninstall removes packages before it rewrites the package list).
As the last step it restores first, ported resources first within it, as today's uninstall does.

Reverse order differs from today's uninstall order elsewhere.
That is safe because every restore either reassigns an existing key, which keeps its position, or removes it; none re-adds a key, so JSON key order does not depend on step order.
The golden check confirms it.

## Managed keys

`managed.py` gives the shapes the restores share, keyed by the marker names markers on disk already use:

- `remember_keys`, `record_keys`, `restore_keys`: top-level keys of one object, with `previous_<name>`, `previous_<name>_present`, and `installed_<name>`; `restore_keys` carries the fallback for markers without the present list. Used by the profile fields and the UI settings, which each had their own copy of the loop.
- `restore_nested`: managed keys inside a nested object, dropping it once empty (terminal, panes, mcp-adapter settings and server, pi-lens tools, open-tui segments, compaction overrides).
- `restore_value`: a whole value install replaced (herdr-agents `models` and `status`).

Where a step's marker names do not fit `previous_<name>` / `installed_<name>`, it passes them explicitly rather than renaming them.

## Phases

1. **Phase 0, delete migrations**, inside `pi-target.py`, with the tests that only covered them.
2. **Phase 1, split into the package**, moving code unchanged apart from imports; tests import modules instead of loading `pi-target.py`.
3. **Phase 2, steps and managed keys**: `steps.py`, `managed.py`, `context.py`, and tests regrouped by module (`tests/pi_packages.py`, `tests/pi_profile.py`, `tests/pi_configs.py`, `tests/pi_resources.py`, `tests/pi_steps.py`, and the new `tests/pi_managed.py`), retiring `tests/pi_review_fixes.py`; shared helpers and the fake npm live in `tests/support/`, outside the `tests/*.py` glob `pi-pins.py` runs.

Each phase is one commit with every suite green and the golden check identical.

## Reality anchor method

`scratch/golden.py` (gitignored; the repository is public and the fixtures hold this machine's state).
It checks out a base ref with `git worktree add` into a temporary directory, then for each fixture home runs `pi-target.py migrate`, `install --skip-external`, and `uninstall --skip-external` once with the base code and once with the working tree, and compares every file under the home after install and after uninstall.

- `PI_AAAAV_ROOT`, `PI_MP_INFRA_ROOT`, and `PI_SDLC_ROOT` are set for both runs so neither depends on its checkout's siblings.
- The worktree path is replaced with the repository path in the base output before comparing, since `LOCAL_PACKAGE` is the checkout's own path.
- Fixtures: an empty home; a synthetic home with user values in every managed file (the shape `tests/install.sh` uses); a copy of this machine's managed files and marker, built at run time and never committed.
- Base ref: the commit before phase 0.
  Phase 0 removals are expected to leave all three fixtures identical, because none holds a legacy-only state; a difference stops the phase for review.

## Risks

- `pi-pins.py auto` runs from launchd at 06:00 and rewrites pins; a broken import would stop updates silently.
  `tests/pi_pins.py` covers it, and the real-home checkpoint runs `pi-pins.py outdated`.
- Tests that patch module attributes (`mock.patch.object(target, "update_mcp")`) must patch the module that defines the name after the split.

## Friction Notes

- Tried: comparing base and working-tree homes after replacing the temporary checkout path.
  Found: macOS resolves `/var` to `/private/var`, and `pi-target.py` resolves `ROOT` and `--home`, so outputs hold the resolved spelling; normalize both.
  Led by: none
- Tried: `git checkout <file>` to undo a deliberate mutation in the golden self-test.
  Found: CC Safety Net blocks it; revert a scripted mutation with the inverse edit instead.
  Led by: none
- Tried: moving function bodies unchanged and calling other modules as `module.function` from `steps.py`.
  Found: `install` had locals named `packages` and `managed`, which shadow the modules of the same name and raise `UnboundLocalError`; pyright flagged the first, an AST scan for locals that match imported modules found the second.
  Led by: this design's "orchestrator calls `module.function`" rule
- Tried: checking the new package with `lens_diagnostics` after adding `pyrightconfig.json`.
  Found: the lens Pyright server keeps the configuration it started with and reports `pi_root` imports and new modules as unresolved; `npx pyright` reads the new file and reports 0 errors.
  Led by: ~/.pi/agent/AGENTS.md "use `lens_diagnostics` for type checks after edits"
- Tried: a shared test helper that put `scripts/` on `sys.path` when imported.
  Found: ruff's import sorting places `from pi_root` before `from support`, so the path must be set in each test file before its imports.
  Led by: none
