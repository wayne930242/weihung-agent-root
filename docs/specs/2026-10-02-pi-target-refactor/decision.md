# pi-target refactor: decisions

## Outcome

`scripts/pi-target.py` (983 lines, 48 functions) and its tests become small modules with one job each, so a new managed setting or package change touches one place and install/uninstall stay symmetric by construction.
The installed result on a machine does not change.

Actor: the repository owner, editing the installer; every machine that runs `scripts/install.sh` or `scripts/uninstall.sh`.

## Scope

In:

- `scripts/pi-target.py` split into a package; `scripts/pi-target.py` stays the entry point.
- `scripts/pi-pins.py` imports that package instead of loading `pi-target.py` through `SourceFileLoader`.
- Upgrade-from-old-state code removed (list in [Removed migrations](#removed-migrations)).
- The repeated "remember previous value, write ours, restore if unchanged" logic becomes one mechanism.
- `install` and `uninstall` become an ordered list of steps; uninstall runs their restores in reverse.
- Tests regrouped by module; `tests/install.sh` and `tests/uninstall.sh` stay as end-to-end checks.

Out:

- `scripts/install.sh` and `scripts/uninstall.sh` behavior, flags, and output.
- What gets installed: packages, pins, settings values, generated `AGENTS.md`, tier roles.
- `pi/extensions/`, skills, rules, agents.
- The launchd schedule of `pi-pins.py auto`.

## Removed migrations

| Code | Why it existed |
|---|---|
| `LEGACY_RENAMES`, `LEGACY_ROOT`, `migrate_legacy_name`, the `migrate` action's rename step | repository renamed from weihung-user-claude |
| `LEGACY_BRIDGE` (`npm:pi-claude-bridge`) | npm bridge replaced by the git fork pin |
| upstream `elidickinson/pi-claude-bridge`, pi-usage, pi-web-access fork, and pi-code fork prefixes in `PINNED_GIT` | upstream and forks replaced by the bridge fork, pi-quotas, and npm releases |
| `RETIRED_PACKAGES` and its removal loop | powerline, notify, pi-usage, pi-todo, standalone Catppuccin theme |
| `retire_powerline` | powerline footer settings |
| `retire_mp_infra_port`, `retire_codebase_memory_port` | resources once ported by hand, now packages or dropped |

Kept, because they serve current behavior rather than old state:

- Retiring other revisions of each current git pin (`PINNED_GIT` with only current prefixes): needed on every pin bump.
- `PI_HERDR_AGENTS_ROOT` override and its displaced-root cleanup.
- Uninstall reading `previous_packages` and `retired_packages` from the marker to restore what the user had before install.
- The fallback for markers without `previous_settings_present` / `previous_ui_settings_present`: this machine's marker has neither key, so its uninstall depends on it.

## Decisions

| Question | Answer | Basis | Status |
|---|---|---|---|
| Delete upgrade-from-old-state migrations? | Yes, all of them | user: other machines are on the latest version; a failure can be recovered from git history | confirmed |
| Keep the marker format readable by the new uninstall? | Yes; existing installs must uninstall cleanly | repository rule: uninstall restores what install replaced | grounded |
| Scope includes `pi-pins.py` and tests? | Yes | planning proposal, accepted with the migration answer | confirmed |
| Who executes? | This session, phase by phase, one commit per phase | planning proposal | confirmed |
| Entry point path | `scripts/pi-target.py` stays; logic moves to `scripts/pi_root/` | `install.sh`, `uninstall.sh`, docs, and the launchd plist call that path | grounded |
| Python version floor | Unchanged: whatever `install.sh` already requires | out of scope | grounded |

No open decisions.
