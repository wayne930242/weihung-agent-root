"""Pi package identity and the packages this repository owns."""

import os
import sys
from pathlib import Path

from .jsonfile import read_json
from .paths import AAAAV, COMPANY_PLUGINS, HERDR_AGENTS_ROOT_VARIABLE, LOCAL_PACKAGE
from .pins import AAAAV_GIT, HERDR_AGENTS_SOURCE, PACKAGES, PINNED_GIT


def package_source(value):
    return value["source"] if isinstance(value, dict) else value


def package_id(value, agent_dir):
    source = package_source(value)
    if source.startswith("npm:"):
        # Pi identifies npm packages by name, so a pinned spec replaces its unpinned predecessor.
        spec = source.removeprefix("npm:")
        return "npm:" + spec[:spec.find("@", 1)] if spec.find("@", 1) > 0 else source
    if source.startswith("git:"):
        return source
    return str((agent_dir / source).resolve())


def unique_packages(values, agent_dir):
    seen = set()
    result = []
    for value in values:
        identity = package_id(value, agent_dir)
        if identity not in seen:
            seen.add(identity)
            result.append(value)
    return result


def obsolete_pin(value):
    source = package_source(value)
    return any(source.startswith(prefixes) and source != current for current, prefixes in PINNED_GIT.items())


def aaaav_source():
    # A machine with an aaaav checkout beside this repo develops against it; any other installs the published repo.
    return str(AAAAV) if AAAAV.exists() else AAAAV_GIT


def plugin_source(name: str, variable: str, default: Path) -> str | None:
    root = Path(os.environ.get(variable, default)).resolve()
    if (root / "package.json").is_file():
        return str(root)
    print(f"{name} not found at {root}; skipped. Set {variable} to the plugin checkout and rerun to add it.", file=sys.stderr)
    return None


def herdr_agents_root():
    """The checkout named by PI_HERDR_AGENTS_ROOT, or None when the variable is unset; a wrong value fails the install."""
    value = os.environ.get(HERDR_AGENTS_ROOT_VARIABLE)
    if not value:
        return None
    root = Path(value).expanduser().resolve()
    manifest = root / "package.json"
    if not manifest.is_file():
        raise ValueError(f"{HERDR_AGENTS_ROOT_VARIABLE}={value} has no package.json at {manifest}; "
                         f"point it at a pi-herdr-agents checkout or unset it to use {HERDR_AGENTS_SOURCE}")
    name = read_json(manifest).get("name")
    if name != "pi-herdr-agents":
        raise ValueError(f"{HERDR_AGENTS_ROOT_VARIABLE}={value} is the package {name!r}, not pi-herdr-agents")
    return str(root)


def owned_packages(state):
    """PACKAGES, with the pinned pi-herdr-agents release swapped for the override checkout the install recorded."""
    return [state["herdr_agents"] if package == HERDR_AGENTS_SOURCE and state.get("herdr_agents") else package
            for package in PACKAGES]


def local_packages(state):
    return [state.get("aaaav", str(AAAAV)), LOCAL_PACKAGE, *(state[key] for key in COMPANY_PLUGINS if state.get(key))]
