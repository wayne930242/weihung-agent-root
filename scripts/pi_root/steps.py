"""Install and uninstall: the order the managed parts are applied and restored in."""

import hashlib
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from . import (
    configs,
    external,
    instructions,
    jsonfile,
    managed,
    packages,
    profile,
    resources,
)
from .configs import UI_SETTINGS
from .paths import COMPANY_PLUGINS, HERDR_AGENTS_ROOT_VARIABLE, LOCAL_PACKAGE, MARKER
from .pins import HERDR_AGENTS_SOURCE, PLAYWRITER
from .profile import FIELDS


def install(home, skip_external, force, herdr_root=None):
    agent_dir = home / ".pi/agent"
    marker_path = home / MARKER
    first_install = not marker_path.exists()
    state = jsonfile.read_json(marker_path)
    state["aaaav"] = packages.aaaav_source()
    # pi identifies an npm package by name but a local one by path, so whichever form the other mode used must leave settings.
    # Old checkouts stay recorded until a run completes, so a run that fails midway still removes them on the next one.
    old_roots = [root for root in dict.fromkeys([*state.get("herdr_agents_displaced", []), state.get("herdr_agents")])
                 if root and root != herdr_root]
    state["herdr_agents_displaced"] = old_roots
    if herdr_root:
        state["herdr_agents"] = herdr_root
        print(f"{HERDR_AGENTS_ROOT_VARIABLE}: using {herdr_root} instead of {HERDR_AGENTS_SOURCE}. "
              "The agents/ role overrides were derived from the 2.0.4 bundled roles; "
              "compare them with the checkout's agents/ if it differs.", file=sys.stderr)
    else:
        state.pop("herdr_agents", None)
    gone = []
    for key, (name, variable, default) in COMPANY_PLUGINS.items():
        if source := packages.plugin_source(name, variable, default):
            state[key] = source
        elif key in state:
            gone.append(state.pop(key))
    settings_path = agent_dir / "settings.json"
    mcp_path = configs.mcp_config_path(agent_dir)
    instructions_path = agent_dir / "AGENTS.md"
    settings = jsonfile.read_json(settings_path)
    previous_packages = state.get("previous_packages", list(settings.get("packages", [])))
    state["previous_packages"] = previous_packages
    state.setdefault("retired_packages", [package for package in settings.get("packages", []) if packages.obsolete_pin(package)])
    state.setdefault("integration_installed", not first_install)
    content = instructions.instructions()
    current_hash = hashlib.sha256(instructions_path.read_bytes()).hexdigest() if instructions_path.exists() else None
    if current_hash and (first_install or current_hash != state.get("instructions_hash")):
        if not force:
            raise ValueError(f"{instructions_path} exists; use --force to back it up")
        backup = home / ".local/state/weihung-agent-root/backups" / datetime.now().astimezone().strftime("%Y%m%d-%H%M%S") / ".pi/agent/AGENTS.md"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(instructions_path, backup)
        state["instructions_backup"] = str(backup)
        jsonfile.write_json(marker_path, state)
    agent_dir.mkdir(parents=True, exist_ok=True)
    if not instructions_path.exists() or instructions_path.read_text() != content:
        instructions_path.write_text(content)
    state["instructions_hash"] = hashlib.sha256(content.encode()).hexdigest()
    # A rerun after a later failure must recognize this file as ours, not back it up over the user's.
    jsonfile.write_json(marker_path, state)
    mcp = jsonfile.read_json(mcp_path)
    configs.update_mcp(mcp, state)
    jsonfile.write_json(mcp_path, mcp)
    configs.update_lens(home, state)
    configs.update_open_tui(home, state)
    profile.update_profile(home, state)
    configs.update_ui(home, state)
    configs.update_compaction(home, state)
    jsonfile.write_json(marker_path, state)
    # The other form of pi-herdr-agents leaves settings even when the user had declared it first.
    retired_ids = {packages.package_id(value, agent_dir) for value in old_roots + ([HERDR_AGENTS_SOURCE] if herdr_root else [])}
    pinned = packages.owned_packages(state)
    if not skip_external:
        external.run(["npm", "install", "-g", "@earendil-works/pi-coding-agent@latest"], home)
        if "playwriter_preinstalled" not in state:
            listed = subprocess.run(["npm", "ls", "-g", "--depth=0", "playwriter"], capture_output=True)
            state["playwriter_preinstalled"] = listed.returncode == 0
            jsonfile.write_json(marker_path, state)
        external.run(["npm", "install", "-g", PLAYWRITER], home)
        external.run(["herdr", "integration", "install", "pi"], home)
        state["integration_installed"] = True
        jsonfile.write_json(marker_path, state)
        for package in pinned:
            external.run(["pi", "install", packages.package_source(package)], home)
        for package in state["retired_packages"]:
            settings = jsonfile.read_json(settings_path)
            if package not in settings.get("packages", []):
                continue
            if package.startswith("git:"):
                settings["packages"] = [value for value in settings["packages"] if value != package]
                jsonfile.write_json(settings_path, settings)
            else:
                external.run(["pi", "remove", package], home)
        for package in jsonfile.read_json(settings_path).get("packages", []):
            if packages.package_id(package, agent_dir) in retired_ids:
                external.run(["pi", "remove", packages.package_source(package)], home)
        external.run(["pi", "install", state["aaaav"]], home)
        resources.install_ported_resources(home, state, force)
        jsonfile.write_json(marker_path, state)
        external.run(["pi", "install", LOCAL_PACKAGE], home)
        for key in COMPANY_PLUGINS:
            if state.get(key):
                external.run_company_plugin("install", home, state[key])
    else:
        settings = jsonfile.read_json(settings_path)
        settings["packages"] = [package for package in packages.unique_packages(settings.get("packages", []) + pinned + packages.local_packages(state), agent_dir) if not packages.obsolete_pin(package)]
        jsonfile.write_json(settings_path, settings)
    settings = jsonfile.read_json(settings_path)
    current = settings.get("packages", [])
    owned = pinned + packages.local_packages(state)
    owned_ids = {packages.package_id(value, agent_dir) for value in owned}
    unmanaged = [value for value in current
                 if packages.package_id(value, agent_dir) not in owned_ids | retired_ids and not packages.obsolete_pin(value)]
    # Registry and git specs are written as declared; `pi install` records a local path relative to the agent directory.
    managed_specs = [source if packages.package_source(source).startswith(("npm:", "git:")) else
               next((value for value in current if packages.package_id(value, agent_dir) == packages.package_id(source, agent_dir)), source)
               for source in owned]
    gone_ids = {packages.package_id(value, agent_dir) for value in gone}
    settings["packages"] = [value for value in packages.unique_packages(unmanaged + managed_specs, agent_dir)
                            if packages.package_id(value, agent_dir) not in gone_ids]
    jsonfile.write_json(settings_path, settings)
    state.pop("herdr_agents_displaced")
    jsonfile.write_json(marker_path, state)


def uninstall(home, skip_external):
    agent_dir = home / ".pi/agent"
    marker_path = home / MARKER
    if not marker_path.exists():
        return
    state = jsonfile.read_json(marker_path)
    resources.uninstall_ported_resources(home, state)
    profile.remove_tier_roles(home, state)
    settings_path = agent_dir / "settings.json"
    mcp_path = configs.mcp_config_path(agent_dir)
    instructions_path = agent_dir / "AGENTS.md"
    if instructions_path.exists() and hashlib.sha256(instructions_path.read_bytes()).hexdigest() == state.get("instructions_hash"):
        instructions_path.unlink()
    backup = state.get("instructions_backup")
    if backup and Path(backup).exists() and not instructions_path.exists():
        shutil.move(backup, instructions_path)
    previous_packages = state.get("previous_packages", [])
    previous_ids = {packages.package_id(value, agent_dir) for value in previous_packages}
    managed_packages = packages.owned_packages(state) + packages.local_packages(state)
    company = [state[key] for key in COMPANY_PLUGINS if state.get(key)]
    owned = {packages.package_id(value, agent_dir) for value in managed_packages} - previous_ids
    if not skip_external:
        installed_ids = {packages.package_id(value, agent_dir) for value in jsonfile.read_json(settings_path).get("packages", [])}
        for package in managed_packages:
            identity = packages.package_id(package, agent_dir)
            if identity in owned and identity in installed_ids:
                if package in company:
                    external.run_company_plugin("remove", home, package)
                else:
                    external.run(["pi", "remove", packages.package_source(package)], home)
        if state.get("integration_installed", True):
            external.run(["herdr", "integration", "uninstall", "pi"], home)
        if not state.get("playwriter_preinstalled", True):
            external.run(["npm", "uninstall", "-g", "playwriter"], home)
    settings = jsonfile.read_json(settings_path)
    # A package the user declared before install keeps the spec they wrote, not the pinned one.
    prior = {packages.package_id(value, agent_dir): value for value in previous_packages}
    settings["packages"] = [prior.get(packages.package_id(package, agent_dir), package) for package in settings.get("packages", [])
                            if packages.package_id(package, agent_dir) not in owned]
    # The override replaced a release the user had declared before install; put that spec back like a retired package.
    displaced = [package for package in previous_packages if state.get("herdr_agents")
                 and packages.package_id(package, agent_dir) == packages.package_id(HERDR_AGENTS_SOURCE, agent_dir)]
    for package in [*state.get("retired_packages", []), *displaced]:
        if package not in settings["packages"]:
            if not skip_external:
                external.run(["pi", "install", package], home)
            settings["packages"].append(package)
    settings["packages"] = packages.unique_packages(
        [package for package in previous_packages if package in settings["packages"]] + settings["packages"], agent_dir
    )
    if not settings["packages"]:
        settings.pop("packages")
    for key in FIELDS:
        if settings.get(key) == state.get("installed_settings", {}).get(key):
            previous = state.get("previous_settings", {}).get(key)
            present = state.get("previous_settings_present")
            was_present = key in present if present is not None else previous is not None
            if was_present:
                settings[key] = previous
            else:
                settings.pop(key, None)
    for key in UI_SETTINGS:
        if settings.get(key) == state.get("installed_ui_settings", {}).get(key):
            previous = state.get("previous_ui_settings", {}).get(key)
            present = state.get("previous_ui_settings_present")
            was_present = key in present if present is not None else previous is not None
            if was_present:
                settings[key] = previous
            else:
                settings.pop(key, None)
    managed.restore_managed_keys(settings, "terminal", state.get("installed_terminal"), state.get("previous_terminal"), ("showTerminalProgress",))
    configs.restore_builtin_mcp(settings, state)
    configs.restore_compaction(settings, state)
    jsonfile.write_json(settings_path, settings)
    configs.restore_lens(home, state)
    configs.restore_open_tui(home, state)
    mcp = jsonfile.read_json(mcp_path)
    configs.restore_mcp(mcp, state)
    if mcp:
        jsonfile.write_json(mcp_path, mcp)
    elif mcp_path.exists():
        mcp_path.unlink()
    config_path = agent_dir / "herdr-agents/config.json"
    config = jsonfile.read_json(config_path)
    if config.get("models") == state.get("installed_models"):
        previous = state.get("previous_models")
        if previous is None:
            config.pop("models", None)
        else:
            config["models"] = previous
    if config.get("status") == state.get("installed_status"):
        previous = state.get("previous_status")
        if previous is None:
            config.pop("status", None)
        else:
            config["status"] = previous
    managed.restore_managed_keys(config, "panes", state.get("installed_panes"), state.get("previous_panes"), ("mode", "direction"))
    if config:
        jsonfile.write_json(config_path, config)
    elif config_path.exists():
        config_path.unlink()
    marker_path.unlink()
