#!/usr/bin/env python3
"""Install and remove the repository-owned Pi configuration."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from copy import deepcopy
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BRIDGE_SOURCE = "git:github.com/wayne930242/pi-claude-bridge@31891e9395e510f583def3bd0e01a663582d59a4"
LEGACY_BRIDGE = "npm:pi-claude-bridge"
# Fork commit adding claude-bridge to /usage (upstream iefnaf/pi-usage#4).
USAGE_SOURCE = "git:github.com/wayne930242/pi-usage@a683c242cf42801c484c9ae6eeb3accdf4b7c696"
BRIDGE_GIT_PREFIXES = ("git:github.com/elidickinson/pi-claude-bridge@", "git:github.com/wayne930242/pi-claude-bridge@")
OPUS_1M = "claude-bridge/claude-opus-5-5"
OPUS_200K = "claude-bridge/claude-200k-opus-5-5"
HAIKU = "claude-bridge/claude-haiku-4-5"
LUNA = "openai-codex/gpt-6-luna"
ONE_M_TIERS = {"main", "complex_clear", "complex_unclear", "academic", "architecture"}
PACKAGES = [
    BRIDGE_SOURCE,
    "npm:pi-herdr-agents",
    "npm:pi-mcp-adapter",
    "npm:pi-intercom",
    "npm:pi-ask-user",
    "npm:@capdiem/pi-todo",
    "npm:catppuccin-pi-theme",
    "npm:pi-open-tui",
    "npm:pi-web-access",
    "npm:pi-lens",
    USAGE_SOURCE,
    "npm:@moyai/pi-session-hoarder",
    "npm:pi-jev-compaction",
]
LOCAL_PACKAGE = str(ROOT)
AAAAV = Path(os.environ.get("PI_AAAAV_ROOT", ROOT.parent / "aaaav"))
AAAAV_GIT = "git:github.com/wayne930242/aaaav"
PROFILE = ROOT / "skills/managing-model-preferences/model-preference-profile.md"
FIELDS = ("defaultProvider", "defaultModel", "defaultThinkingLevel")
UI_SETTINGS = {"theme": "catppuccin-mocha", "editorPaddingX": 1, "collapseChangelog": True}
# Packages earlier installs registered and this configuration dropped: pi-open-tui replaces the
# powerline footer, pi-notify wrote escapes into `pi -p` output from every worker pane, and the
# pi-usage fork replaces its npm release, which would otherwise register a second /usage.
RETIRED_PACKAGES = ["npm:pi-powerline-footer", "npm:pi-notify", "npm:pi-usage"]
MP_INFRA = ROOT.parent / "moldplan-center/plugins/waydosoft-marketplace/plugins/mp-infra"
TTT_PREFIX = Path(".local/share/weihung-user-claude/team-toon-tack")
# pi-skills ships bare skill directories without a pi manifest; its README installs it as a clone under the skills root.
PI_SKILLS_GIT = os.environ.get("PI_SKILLS_GIT", "https://github.com/badlogic/pi-skills.git")
PI_SKILLS_CLONE = Path(".local/share/weihung-user-claude/pi-skills")


def package_id(value, agent_dir):
    if value.startswith("npm:"):
        return value
    if value.startswith("git:"):
        return value
    return str((agent_dir / value).resolve())


def obsolete_bridge(value):
    return value == LEGACY_BRIDGE or (
        value.startswith(BRIDGE_GIT_PREFIXES)
        and value != BRIDGE_SOURCE
    )


def read_json(path):
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if not path.exists() or path.read_text() != content:
        path.write_text(content)


def restore_managed_keys(container, key, installed, previous, managed_keys):
    current = container.get(key)
    if not isinstance(current, dict) or not isinstance(installed, dict):
        return
    restored = deepcopy(current)
    prior = previous if isinstance(previous, dict) else {}
    for name in managed_keys:
        if current.get(name) != installed.get(name):
            continue
        if name in prior:
            restored[name] = deepcopy(prior[name])
        else:
            restored.pop(name, None)
    if restored:
        container[key] = restored
    else:
        container.pop(key, None)


def run(args, home):
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PI_CODING_AGENT_DIR"] = str(home / ".pi/agent")
    subprocess.run(args, check=True, env=env)


def managed_resource(home, state, destination, source, force=False, link=False):
    """Install a file or link while retaining a user-owned predecessor."""
    key = str(destination.relative_to(home))
    records = state.setdefault("ported_resources", {})
    record = records.get(key)
    if destination.exists() or destination.is_symlink():
        current = (destination.readlink().as_posix() if destination.is_symlink() else
                   hashlib.sha256(destination.read_bytes()).hexdigest() if destination.is_file() else None)
        if record and current == record["installed"]:
            destination.unlink()
        elif not record and ((link and destination.is_symlink() and current == str(source)) or
                             (not link and destination.is_file() and current == hashlib.sha256(source).hexdigest())):
            return
        else:
            if not force:
                raise ValueError(f"{destination} exists; use --force to back it up")
            backup = home / ".local/state/weihung-user-claude/backups" / datetime.now().strftime("%Y%m%d-%H%M%S") / key
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(destination, backup)
            record = {**(record or {}), "backup": str(backup)}
    destination.parent.mkdir(parents=True, exist_ok=True)
    if link:
        destination.symlink_to(source)
        installed = str(source)
    else:
        destination.write_bytes(source)
        installed = hashlib.sha256(source).hexdigest()
    records[key] = {**(record or {}), "installed": installed, "link": link}
    write_json(home / ".pi/agent/.weihung-user-claude.json", state)


def aaaav_source():
    # A machine with an aaaav checkout beside this repo develops against it; any other installs the published repo.
    return str(AAAAV) if AAAAV.exists() else AAAAV_GIT


def install_ported_resources(home, state, force):
    agent_dir = home / ".pi/agent"
    mp_root = Path(os.environ.get("PI_MP_INFRA_ROOT", MP_INFRA)).resolve()
    has_mp_infra = (mp_root / "hooks/production-safety-hook").is_file()
    if not has_mp_infra:
        print(f"mp-infra not found at {mp_root}; skipped its skills and hooks. "
              "Set PI_MP_INFRA_ROOT to the plugin checkout and rerun to add them.", file=sys.stderr)
    prefix = home / TTT_PREFIX
    run(["npm", "install", "--prefix", str(prefix), "--no-save", "--no-package-lock", "team-toon-tack@latest"], home)
    ttt_root = prefix / "node_modules/team-toon-tack"
    if not (ttt_root / "skills/managing-linear-tasks/SKILL.md").is_file():
        raise ValueError(f"team-toon-tack package is missing: {ttt_root}")
    state["ttt_prefix"] = str(prefix)
    write_json(agent_dir / ".weihung-user-claude.json", state)

    # The official installer generates Pi's current extension and skill in a staging HOME.
    # Our generated AGENTS.md remains the sole owner of Pi instructions.
    with tempfile.TemporaryDirectory(prefix="pi-cbmem-") as temporary:
        stage = Path(temporary)
        env = {**os.environ, "HOME": str(stage), "XDG_CACHE_HOME": str(stage / ".cache")}
        binary = home / ".local/bin/codebase-memory-mcp"
        if not binary.is_file():
            raise ValueError(f"codebase-memory-mcp binary is missing: {binary}")
        subprocess.run([str(binary), "install", "--clients=pi", "-y"], check=True, env=env,
                       stdout=subprocess.DEVNULL)
        for relative in ("extensions/cbmem.ts", "skills/codebase-memory/SKILL.md"):
            source = stage / ".pi/agent" / relative
            if not source.is_file():
                raise ValueError(f"official codebase-memory Pi resource is missing: {relative}")
            content = source.read_text()
            if relative.endswith("cbmem.ts"):
                staged_binary = str(stage / ".local/bin/codebase-memory-mcp")
                if staged_binary not in content:
                    raise ValueError("official Pi extension did not identify its staged binary")
                content = content.replace(staged_binary, str(binary))
            managed_resource(home, state, agent_dir / relative, content.encode(), force)

    if has_mp_infra:
        managed_resource(home, state, agent_dir / "mp-infra.json", (json.dumps({"root": str(mp_root)}, indent=2) + "\n").encode(), force)
        for skill in sorted((mp_root / "skills").iterdir()):
            if (skill / "SKILL.md").is_file():
                managed_resource(home, state, agent_dir / "skills" / skill.name, skill, force, link=True)
    managed_resource(home, state, agent_dir / "skills/managing-linear-tasks", ttt_root / "skills/managing-linear-tasks", force, link=True)
    for command in sorted((ttt_root / "commands").glob("ttt-*.md")):
        action = ("Create the resulting project skill under `.agents/skills/` for Pi."
                  if command.stem == "ttt-write-work-on-skill" else
                  f"Use Pi's shell tool and `{home / '.local/bin/ttt'}` for the matching CLI operation.")
        prompt = (f"---\ndescription: Run team-toon-tack {command.stem.removeprefix('ttt-')}\n"
                  f"argument-hint: '[arguments]'\n---\n"
                  f"Read and follow `{command}` for this request. Interpret its `{{{{ ... }}}}` placeholders "
                  "from these arguments: $ARGUMENTS. Translate `/ttt:*` references to Pi's `/ttt-*` templates. "
                  f"{action}\n")
        managed_resource(home, state, agent_dir / "prompts" / command.name, prompt.encode(), force)
    cli = prefix / "node_modules/.bin/ttt"
    if not cli.exists():
        raise ValueError(f"team-toon-tack CLI is missing: {cli}")
    managed_resource(home, state, home / ".local/bin/ttt", cli, force, link=True)
    clone = home / PI_SKILLS_CLONE
    if (clone / ".git").is_dir():
        run(["git", "-C", str(clone), "pull", "-q", "--ff-only"], home)
    else:
        run(["git", "clone", "-q", "--depth", "1", PI_SKILLS_GIT, str(clone)], home)
    state["pi_skills_clone"] = str(clone)
    write_json(agent_dir / ".weihung-user-claude.json", state)
    managed_resource(home, state, agent_dir / "skills/pi-skills", clone, force, link=True)


def uninstall_ported_resources(home, state):
    for key, record in reversed(list(state.get("ported_resources", {}).items())):
        destination = home / key
        if destination.is_symlink():
            current = destination.readlink().as_posix()
        elif destination.is_file():
            current = hashlib.sha256(destination.read_bytes()).hexdigest()
        else:
            continue
        if current != record["installed"]:
            continue
        destination.unlink()
        backup = record.get("backup")
        if backup and Path(backup).exists():
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(backup, destination)
    prefix = state.get("ttt_prefix")
    if prefix and Path(prefix) == home / TTT_PREFIX and Path(prefix).exists():
        shutil.rmtree(prefix)
    clone = state.get("pi_skills_clone")
    if clone and Path(clone) == home / PI_SKILLS_CLONE and Path(clone).exists():
        shutil.rmtree(clone)


def active_strategy():
    match = re.search(r"^Active strategy: \[[^]]+\]\(strategies/([^)]+)\)", PROFILE.read_text(), re.M)
    if not match:
        raise ValueError("active strategy is missing from model-preference-profile.md")
    return match.group(1).removesuffix(".md")


def routing():
    strategy = active_strategy()
    profiles = read_json(ROOT / "pi/model-profiles.json")
    if strategy not in profiles:
        raise ValueError(f"no Pi profile for strategy {strategy}")
    tiers = profiles[strategy]
    default = tiers["main"]
    categories = {name: tiers[name] for name in ("coding", "review", "recon", "docs")}
    categories.update(qa=tiers["review"], architecture=tiers["complex_unclear"])
    tasks = {name: candidates(model, name) for name, (model, _) in categories.items()}
    return strategy, default, tiers, tasks


def candidates(model, tier):
    codex_fallback = {
        "docs": LUNA,
        "recon": LUNA,
        "simple": LUNA,
        "complex_unclear": "openai-codex/gpt-6-astra",
        "architecture": "openai-codex/gpt-6-astra",
        "academic": "openai-codex/gpt-6-astra",
    }.get(tier, "openai-codex/gpt-6-sol")
    if model.startswith("claude-bridge/"):
        other = codex_fallback
    elif model == LUNA:
        other = HAIKU
    else:
        other = OPUS_1M if tier in ONE_M_TIERS else OPUS_200K
    return list(dict.fromkeys((model, other)))


def default_candidates(default):
    return candidates(default[0], "main")


def instructions():
    body = (ROOT / "pi/AGENTS.md.in").read_text().rstrip()
    strategy, default, profile_tiers, tasks = routing()
    tier_lines = [f"- Main: model `{', '.join(default_candidates(default))}`; thinking `{default[1]}`."]
    for name, (model, thinking) in profile_tiers.items():
        if name == "main":
            continue
        tier_lines.append(f"- {name}: model `{', '.join(candidates(model, name))}`; thinking `{thinking}`.")
    guidance = "For subagent dispatch, pass the selected tier's full comma-separated list as the `model` value and its thinking level as `thinking`. The `task:<category>` shorthand is available only for coding, review, recon, qa, architecture, and docs."
    return body + f"\n\n## Active model strategy: {strategy}\n\n" + guidance + "\n\n" + "\n".join(tier_lines) + "\n"


def update_profile(home, state):
    agent_dir = home / ".pi/agent"
    settings_path = agent_dir / "settings.json"
    config_path = agent_dir / "herdr-agents/config.json"
    settings = read_json(settings_path)
    config = read_json(config_path)
    strategy, default, tiers, tasks = routing()
    if "previous_settings" not in state:
        state["previous_settings"] = {key: settings.get(key) for key in FIELDS}
        state["previous_settings_present"] = [key for key in FIELDS if key in settings]
    state.setdefault("previous_models", deepcopy(config.get("models")))
    state.setdefault("previous_status", deepcopy(config.get("status")))
    provider, model = default[0].split("/", 1)
    settings.update(defaultProvider=provider, defaultModel=model, defaultThinkingLevel=default[1])
    models = config.setdefault("models", {})
    models["default"] = ", ".join(default_candidates(default))
    models.setdefault("agents", {})
    models["tasks"] = tasks
    config.setdefault("status", {"enabled": True})
    write_json(settings_path, settings)
    write_json(config_path, config)
    state["installed_settings"] = {key: settings[key] for key in FIELDS}
    state["installed_models"] = deepcopy(models)
    state["installed_status"] = deepcopy(config["status"])
    state["strategy"] = strategy


def retire_powerline(settings, state):
    """Return the powerline queue setting an earlier install managed to its prior value."""
    current = settings.get("powerline")
    if isinstance(current, dict) and "installed_powerline" in state:
        previous = state.get("previous_powerline") or {}
        restore_managed_keys(current, "queue", (state.get("installed_powerline") or {}).get("queue"), previous.get("queue"), ("compactPromptMode",))
        if not current:
            settings.pop("powerline", None)
    state.pop("installed_powerline", None)
    state.pop("previous_powerline", None)


def update_ui(home, state):
    agent_dir = home / ".pi/agent"
    settings_path = agent_dir / "settings.json"
    config_path = agent_dir / "herdr-agents/config.json"
    settings = read_json(settings_path)
    config = read_json(config_path)
    if "previous_ui_settings" not in state:
        state["previous_ui_settings"] = {key: deepcopy(settings.get(key)) for key in UI_SETTINGS}
        state["previous_ui_settings_present"] = [key for key in UI_SETTINGS if key in settings]
    state.setdefault("previous_terminal", deepcopy(settings.get("terminal")))
    state.setdefault("previous_panes", deepcopy(config.get("panes")))
    settings.update(UI_SETTINGS)
    settings.setdefault("terminal", {})["showTerminalProgress"] = True
    retire_powerline(settings, state)
    config["panes"] = {**config.get("panes", {}), "mode": "split", "direction": "right"}
    write_json(settings_path, settings)
    write_json(config_path, config)
    state["installed_ui_settings"] = {key: deepcopy(settings[key]) for key in UI_SETTINGS}
    state["installed_terminal"] = deepcopy(settings["terminal"])
    state["installed_panes"] = deepcopy(config["panes"])


def install(home, skip_external, force):
    agent_dir = home / ".pi/agent"
    marker_path = agent_dir / ".weihung-user-claude.json"
    first_install = not marker_path.exists()
    state = read_json(marker_path)
    state["aaaav"] = aaaav_source()
    settings_path = agent_dir / "settings.json"
    mcp_path = agent_dir / "mcp.json"
    instructions_path = agent_dir / "AGENTS.md"
    settings = read_json(settings_path)
    previous_packages = state.get("previous_packages", list(settings.get("packages", [])))
    state["previous_packages"] = previous_packages
    state.setdefault("retired_packages", [package for package in settings.get("packages", []) if obsolete_bridge(package)])
    state.setdefault("integration_installed", not first_install)
    content = instructions()
    current_hash = hashlib.sha256(instructions_path.read_bytes()).hexdigest() if instructions_path.exists() else None
    if current_hash and (first_install or current_hash != state.get("instructions_hash")):
        if not force:
            raise ValueError(f"{instructions_path} exists; use --force to back it up")
        backup = home / ".local/state/weihung-user-claude/backups" / datetime.now().strftime("%Y%m%d-%H%M%S") / ".pi/agent/AGENTS.md"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(instructions_path, backup)
        state["instructions_backup"] = str(backup)
    agent_dir.mkdir(parents=True, exist_ok=True)
    if not instructions_path.exists() or instructions_path.read_text() != content:
        instructions_path.write_text(content)
    state["instructions_hash"] = hashlib.sha256(content.encode()).hexdigest()
    mcp = read_json(mcp_path)
    state.setdefault("previous_discovery", mcp.get("settings", {}).get("hostConfigDiscovery"))
    mcp.setdefault("settings", {})["hostConfigDiscovery"] = "on"
    write_json(mcp_path, mcp)
    update_profile(home, state)
    update_ui(home, state)
    write_json(marker_path, state)
    if not skip_external:
        run(["npm", "install", "-g", "@earendil-works/pi-coding-agent@latest"], home)
        run(["herdr", "integration", "install", "pi"], home)
        state["integration_installed"] = True
        write_json(marker_path, state)
        for package in PACKAGES:
            run(["pi", "install", package], home)
        for package in state["retired_packages"]:
            settings = read_json(settings_path)
            if package not in settings.get("packages", []):
                continue
            if package.startswith("git:"):
                settings["packages"] = [value for value in settings["packages"] if value != package]
                write_json(settings_path, settings)
            else:
                run(["pi", "remove", package], home)
        for package in RETIRED_PACKAGES:
            if package in read_json(settings_path).get("packages", []) and package not in state["previous_packages"]:
                run(["pi", "remove", package], home)
        run(["pi", "install", state["aaaav"]], home)
        install_ported_resources(home, state, force)
        write_json(marker_path, state)
        run(["pi", "install", LOCAL_PACKAGE], home)
    else:
        settings = read_json(settings_path)
        settings["packages"] = [package for package in dict.fromkeys(settings.get("packages", []) + PACKAGES + [state["aaaav"], LOCAL_PACKAGE]) if not obsolete_bridge(package)]
        write_json(settings_path, settings)
    settings = read_json(settings_path)
    current = settings.get("packages", [])
    owned = PACKAGES + [state["aaaav"], LOCAL_PACKAGE]
    owned_ids = {package_id(value, agent_dir) for value in owned}
    retired = [package for package in RETIRED_PACKAGES if package not in state["previous_packages"]]
    unmanaged = [value for value in current
                 if package_id(value, agent_dir) not in owned_ids and not obsolete_bridge(value) and value not in retired]
    managed = [next((value for value in current if package_id(value, agent_dir) == package_id(source, agent_dir)), source) for source in owned]
    settings["packages"] = list(dict.fromkeys(unmanaged + managed))
    write_json(settings_path, settings)
    write_json(marker_path, state)


def uninstall(home, skip_external):
    agent_dir = home / ".pi/agent"
    marker_path = agent_dir / ".weihung-user-claude.json"
    if not marker_path.exists():
        return
    state = read_json(marker_path)
    uninstall_ported_resources(home, state)
    settings_path = agent_dir / "settings.json"
    mcp_path = agent_dir / "mcp.json"
    instructions_path = agent_dir / "AGENTS.md"
    if instructions_path.exists() and hashlib.sha256(instructions_path.read_bytes()).hexdigest() == state.get("instructions_hash"):
        instructions_path.unlink()
        backup = state.get("instructions_backup")
        if backup and Path(backup).exists():
            shutil.move(backup, instructions_path)
    previous_packages = state.get("previous_packages", [])
    previous_ids = {package_id(value, agent_dir) for value in previous_packages}
    managed_packages = PACKAGES + [state.get("aaaav", str(AAAAV)), LOCAL_PACKAGE]
    owned = {package_id(value, agent_dir) for value in managed_packages} - previous_ids
    if not skip_external:
        installed_ids = {package_id(value, agent_dir) for value in read_json(settings_path).get("packages", [])}
        for package in managed_packages:
            identity = package_id(package, agent_dir)
            if identity in owned and identity in installed_ids:
                run(["pi", "remove", package], home)
        if state.get("integration_installed", True):
            run(["herdr", "integration", "uninstall", "pi"], home)
    settings = read_json(settings_path)
    settings["packages"] = [package for package in settings.get("packages", []) if package_id(package, agent_dir) not in owned]
    for package in state.get("retired_packages", []):
        if package not in settings["packages"]:
            if not skip_external:
                run(["pi", "install", package], home)
            settings["packages"].append(package)
    settings["packages"] = list(dict.fromkeys(
        [package for package in previous_packages if package in settings["packages"]] + settings["packages"]
    ))
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
    restore_managed_keys(settings, "terminal", state.get("installed_terminal"), state.get("previous_terminal"), ("showTerminalProgress",))
    retire_powerline(settings, state)
    write_json(settings_path, settings)
    mcp = read_json(mcp_path)
    if mcp.get("settings", {}).get("hostConfigDiscovery") == "on":
        previous = state.get("previous_discovery")
        if previous is None:
            mcp["settings"].pop("hostConfigDiscovery", None)
        else:
            mcp["settings"]["hostConfigDiscovery"] = previous
    if mcp.get("settings") == {}:
        mcp.pop("settings")
    if mcp:
        write_json(mcp_path, mcp)
    elif mcp_path.exists():
        mcp_path.unlink()
    config_path = agent_dir / "herdr-agents/config.json"
    config = read_json(config_path)
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
    restore_managed_keys(config, "panes", state.get("installed_panes"), state.get("previous_panes"), ("mode", "direction"))
    if config:
        write_json(config_path, config)
    elif config_path.exists():
        config_path.unlink()
    marker_path.unlink()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("install", "uninstall", "apply-profile"))
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--skip-external", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    if args.action == "install":
        install(home, args.skip_external, args.force)
    elif args.action == "uninstall":
        uninstall(home, args.skip_external)
    else:
        marker_path = home / ".pi/agent/.weihung-user-claude.json"
        state = read_json(marker_path)
        if not state:
            raise ValueError("Pi target is not installed")
        instructions_path = home / ".pi/agent/AGENTS.md"
        if hashlib.sha256(instructions_path.read_bytes()).hexdigest() != state.get("instructions_hash"):
            raise ValueError("Pi instructions changed since installation; inspect the file before applying a profile")
        update_profile(home, state)
        instructions_path.write_text(instructions())
        state["instructions_hash"] = hashlib.sha256(instructions().encode()).hexdigest()
        write_json(marker_path, state)


if __name__ == "__main__":
    main()
