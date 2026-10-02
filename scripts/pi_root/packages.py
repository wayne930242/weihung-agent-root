"""Pi packages: identity, the packages this repository owns, and the install step that also brings the tools they need."""

import os
import subprocess
import sys
from pathlib import Path

from . import external, resources
from .context import Context, State
from .jsonfile import read_json, write_json
from .paths import AAAAV, COMPANY_PLUGINS, HERDR_AGENTS_ROOT_VARIABLE, LOCAL_PACKAGE
from .pins import AAAAV_GIT, HERDR_AGENTS_SOURCE, PACKAGES, PINNED_GIT, PLAYWRITER

Package = str | dict


def package_source(value: Package) -> str:
    return value["source"] if isinstance(value, dict) else value


def package_id(value: Package, agent_dir: Path) -> str:
    source = package_source(value)
    if source.startswith("npm:"):
        # Pi identifies npm packages by name, so a pinned spec replaces its unpinned predecessor.
        spec = source.removeprefix("npm:")
        return "npm:" + spec[:spec.find("@", 1)] if spec.find("@", 1) > 0 else source
    if source.startswith("git:"):
        return source
    return str((agent_dir / source).resolve())


def unique_packages(values: list[Package], agent_dir: Path) -> list[Package]:
    seen = set()
    result = []
    for value in values:
        identity = package_id(value, agent_dir)
        if identity not in seen:
            seen.add(identity)
            result.append(value)
    return result


def obsolete_pin(value: Package) -> bool:
    source = package_source(value)
    return any(source.startswith(prefixes) and source != current for current, prefixes in PINNED_GIT.items())


def aaaav_source() -> str:
    # A machine with an aaaav checkout beside this repo develops against it; any other installs the published repo.
    return str(AAAAV) if AAAAV.exists() else AAAAV_GIT


def plugin_source(name: str, variable: str, default: Path) -> str | None:
    root = Path(os.environ.get(variable, default)).resolve()
    if (root / "package.json").is_file():
        return str(root)
    print(f"{name} not found at {root}; skipped. Set {variable} to the plugin checkout and rerun to add it.", file=sys.stderr)
    return None


def herdr_agents_root() -> str | None:
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


def owned_packages(state: State) -> list[Package]:
    """PACKAGES, with the pinned pi-herdr-agents release swapped for the override checkout the install recorded."""
    return [state["herdr_agents"] if package == HERDR_AGENTS_SOURCE and state.get("herdr_agents") else package
            for package in PACKAGES]


def local_packages(state: State) -> list[Package]:
    return [state.get("aaaav", str(AAAAV)), LOCAL_PACKAGE, *(state[key] for key in COMPANY_PLUGINS if state.get(key))]


def plan(ctx: Context) -> None:
    """Record which package sources this run uses and what settings held before the first install."""
    state = ctx.state
    herdr_root = ctx.herdr_root
    state["aaaav"] = aaaav_source()
    # pi identifies an npm package by name but a local one by path, so whichever form the other mode used must leave settings.
    # Old checkouts stay recorded until a run completes, so a run that fails midway still removes them on the next one.
    state["herdr_agents_displaced"] = [root for root in dict.fromkeys([*state.get("herdr_agents_displaced", []), state.get("herdr_agents")])
                                       if root and root != herdr_root]
    if herdr_root:
        state["herdr_agents"] = herdr_root
        print(f"{HERDR_AGENTS_ROOT_VARIABLE}: using {herdr_root} instead of {HERDR_AGENTS_SOURCE}. "
              "The agents/ role overrides were derived from the 2.0.4 bundled roles; "
              "compare them with the checkout's agents/ if it differs.", file=sys.stderr)
    else:
        state.pop("herdr_agents", None)
    for key, (name, variable, default) in COMPANY_PLUGINS.items():
        if source := plugin_source(name, variable, default):
            state[key] = source
        elif key in state:
            ctx.gone_plugins.append(state.pop(key))
    settings = read_json(ctx.settings_path)
    state["previous_packages"] = state.get("previous_packages", list(settings.get("packages", [])))
    state.setdefault("retired_packages", [package for package in settings.get("packages", []) if obsolete_pin(package)])
    state.setdefault("integration_installed", not ctx.first_install)


def apply(ctx: Context) -> None:
    """Install pi, its tools, and every owned package, then write the package list in the order pi expects."""
    home, state, agent_dir, settings_path = ctx.home, ctx.state, ctx.agent_dir, ctx.settings_path
    old_roots = state["herdr_agents_displaced"]
    # The other form of pi-herdr-agents leaves settings even when the user had declared it first.
    retired_ids = {package_id(value, agent_dir) for value in old_roots + ([HERDR_AGENTS_SOURCE] if ctx.herdr_root else [])}
    pinned = owned_packages(state)
    if not ctx.skip_external:
        external.run(["npm", "install", "-g", "@earendil-works/pi-coding-agent@latest"], home)
        if "playwriter_preinstalled" not in state:
            listed = subprocess.run(["npm", "ls", "-g", "--depth=0", "playwriter"], capture_output=True, check=False)
            state["playwriter_preinstalled"] = listed.returncode == 0
            ctx.save()
        external.run(["npm", "install", "-g", PLAYWRITER], home)
        external.run(["herdr", "integration", "install", "pi"], home)
        state["integration_installed"] = True
        ctx.save()
        for package in pinned:
            external.run(["pi", "install", package_source(package)], home)
        for package in state["retired_packages"]:
            settings = read_json(settings_path)
            if package not in settings.get("packages", []):
                continue
            if package.startswith("git:"):
                settings["packages"] = [value for value in settings["packages"] if value != package]
                write_json(settings_path, settings)
            else:
                external.run(["pi", "remove", package], home)
        for package in read_json(settings_path).get("packages", []):
            if package_id(package, agent_dir) in retired_ids:
                external.run(["pi", "remove", package_source(package)], home)
        external.run(["pi", "install", state["aaaav"]], home)
        resources.install_ported_resources(home, state, ctx.force)
        ctx.save()
        external.run(["pi", "install", LOCAL_PACKAGE], home)
        for key in COMPANY_PLUGINS:
            if state.get(key):
                external.run_company_plugin("install", home, state[key])
    else:
        settings = read_json(settings_path)
        settings["packages"] = [package for package in unique_packages(settings.get("packages", []) + pinned + local_packages(state), agent_dir)
                                if not obsolete_pin(package)]
        write_json(settings_path, settings)
    settings = read_json(settings_path)
    current = settings.get("packages", [])
    owned = pinned + local_packages(state)
    owned_ids = {package_id(value, agent_dir) for value in owned}
    unmanaged = [value for value in current
                 if package_id(value, agent_dir) not in owned_ids | retired_ids and not obsolete_pin(value)]
    # Registry and git specs are written as declared; `pi install` records a local path relative to the agent directory.
    declared = [source if package_source(source).startswith(("npm:", "git:")) else
                next((value for value in current if package_id(value, agent_dir) == package_id(source, agent_dir)), source)
                for source in owned]
    gone_ids = {package_id(value, agent_dir) for value in ctx.gone_plugins}
    settings["packages"] = [value for value in unique_packages(unmanaged + declared, agent_dir)
                            if package_id(value, agent_dir) not in gone_ids]
    write_json(settings_path, settings)
    state.pop("herdr_agents_displaced")


def restore(ctx: Context) -> None:
    """Remove what install added and put back the packages and tools the user had before it."""
    home, state, agent_dir, settings_path = ctx.home, ctx.state, ctx.agent_dir, ctx.settings_path
    resources.uninstall_ported_resources(home, state)
    previous_packages = state.get("previous_packages", [])
    previous_ids = {package_id(value, agent_dir) for value in previous_packages}
    managed_packages = owned_packages(state) + local_packages(state)
    company = [state[key] for key in COMPANY_PLUGINS if state.get(key)]
    owned = {package_id(value, agent_dir) for value in managed_packages} - previous_ids
    if not ctx.skip_external:
        installed_ids = {package_id(value, agent_dir) for value in read_json(settings_path).get("packages", [])}
        for package in managed_packages:
            identity = package_id(package, agent_dir)
            if identity in owned and identity in installed_ids:
                if package in company:
                    external.run_company_plugin("remove", home, package_source(package))
                else:
                    external.run(["pi", "remove", package_source(package)], home)
        if state.get("integration_installed", True):
            external.run(["herdr", "integration", "uninstall", "pi"], home)
        if not state.get("playwriter_preinstalled", True):
            external.run(["npm", "uninstall", "-g", "playwriter"], home)
    settings = read_json(settings_path)
    # A package the user declared before install keeps the spec they wrote, not the pinned one.
    prior = {package_id(value, agent_dir): value for value in previous_packages}
    settings["packages"] = [prior.get(package_id(package, agent_dir), package) for package in settings.get("packages", [])
                            if package_id(package, agent_dir) not in owned]
    # The override replaced a release the user had declared before install; put that spec back like a retired package.
    displaced = [package for package in previous_packages if state.get("herdr_agents")
                 and package_id(package, agent_dir) == package_id(HERDR_AGENTS_SOURCE, agent_dir)]
    for package in [*state.get("retired_packages", []), *displaced]:
        if package not in settings["packages"]:
            if not ctx.skip_external:
                external.run(["pi", "install", package], home)
            settings["packages"].append(package)
    settings["packages"] = unique_packages(
        [package for package in previous_packages if package in settings["packages"]] + settings["packages"], agent_dir
    )
    if not settings["packages"]:
        settings.pop("packages")
    write_json(settings_path, settings)
