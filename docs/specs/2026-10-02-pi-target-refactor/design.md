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
| `managed.py` | the managed-key mechanism: record previous once, record installed, restore when unchanged | `remember_previous`, `restore_managed_keys`, and the inline restore loops in `uninstall` |
| `packages.py` | identity (`package_source`, `package_id`, `unique_packages`, `obsolete_pin`), owned and local package lists, the install and uninstall package steps | package helpers and the package parts of `install` / `uninstall` |
| `external.py` | `run` and the calls to npm, pi, herdr, and Playwriter | `run`, `run_company_plugin`, the external block of `install` |
| `profile.py` | strategy routing, candidates, enabled models, tier roles, the profile step | `routing` … `update_profile`, its restore in `uninstall` |
| `instructions.py` | generated `AGENTS.md`, its backup and restore | the instructions parts of `install`, `uninstall`, and `apply-profile` |
| `configs.py` | the small config steps: UI and terminal and panes, built-in MCP off, mcp-adapter, pi-lens, open-tui, compaction | `update_*` / `restore_*` pairs |
| `resources.py` | `managed_resource`, ported team-toon-tack and pi-skills resources, their restore | same names |
| `steps.py` | `Step` and the ordered step list; `install` and `uninstall` run it | `install`, `uninstall` |
| `cli.py` | argparse and the four actions | `main` |

`scripts/pi-pins.py` imports `pi_root.pins` and `pi_root.packages` and rewrites pins in `pi_root/pins.py` instead of `pi-target.py`.

## Step interface

```python
class Context(NamedTuple):
    home: Path
    state: dict          # the marker, saved by the runner after every step
    skip_external: bool
    force: bool
    herdr_root: str | None

class Step(NamedTuple):
    name: str
    apply: Callable[[Context], None]
    restore: Callable[[Context], None]
```

`install` runs `apply` in list order and saves the marker after each step.
`uninstall` runs `restore` in reverse list order, then deletes the marker.
The list order is today's install order, so fresh-install files keep their key order: instructions, mcp-adapter, pi-lens, open-tui, profile, UI, compaction, packages and external tools, ported resources.

Reverse order differs from today's uninstall order.
That is safe because every restore either reassigns an existing key, which keeps its position, or removes it; none re-adds a key, so JSON key order does not depend on step order.
The golden check confirms it.

## Managed keys

Today six places record a previous value and later restore it, each in its own shape.
`managed.py` gives one shape, keyed by the marker names in use today so existing markers keep working:

```python
def remember(state: dict, name: str, container: dict, keys: Iterable[str]) -> None
def record_installed(state: dict, name: str, container: dict, keys: Iterable[str]) -> None
def restore(state: dict, name: str, container: dict, keys: Iterable[str]) -> None
```

A step that manages keys inside a nested object passes that object as `container`.
Marker key names (`previous_ui_settings`, `installed_terminal`, …) are fixed by the existing markers; where today's names do not fit the `previous_<name>` / `installed_<name>` pattern, the step passes them explicitly rather than renaming them.

## Phases

1. **Phase 0, delete migrations**, inside `pi-target.py`, with the tests that only covered them.
2. **Phase 1, split into the package**, moving code unchanged apart from imports; tests import modules instead of loading `pi-target.py`.
3. **Phase 2, steps and managed keys**: `steps.py`, `managed.py`, and tests regrouped by module (`tests/pi_packages.py`, `tests/pi_profile.py`, `tests/pi_configs.py`, `tests/pi_resources.py`, `tests/pi_steps.py`), retiring `tests/pi_review_fixes.py`.

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
