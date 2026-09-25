#!/usr/bin/env python3
"""Install and remove the repository-owned Pi configuration."""

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from copy import deepcopy
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BRIDGE_SOURCE = "git:github.com/elidickinson/pi-claude-bridge@227f5eb4450a070dfbc083a7fe75b8b35366b941"
LEGACY_BRIDGE = "npm:pi-claude-bridge"
PACKAGES = [
    BRIDGE_SOURCE,
    "npm:pi-herdr-agents",
    "npm:pi-mcp-adapter",
    "npm:pi-intercom",
    "npm:pi-ask-user",
    "npm:@capdiem/pi-todo",
]
LOCAL_PACKAGE = str(ROOT)
AAAAV = ROOT.parent / "aaaav"
PROFILE = ROOT / "skills/managing-model-preferences/model-preference-profile.md"
FIELDS = ("defaultProvider", "defaultModel", "defaultThinkingLevel")


def package_id(value, agent_dir):
    if value.startswith("npm:"):
        return value
    if value.startswith("git:"):
        return value
    return str((agent_dir / value).resolve())


def obsolete_bridge(value):
    return value == LEGACY_BRIDGE or (
        value.startswith("git:github.com/elidickinson/pi-claude-bridge@")
        and value != BRIDGE_SOURCE
    )


def read_json(path):
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if not path.exists() or path.read_text() != content:
        path.write_text(content)


def run(args, home):
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PI_CODING_AGENT_DIR"] = str(home / ".pi/agent")
    subprocess.run(args, check=True, env=env)


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
        "docs": "openai-codex/gpt-6-luna",
        "recon": "openai-codex/gpt-6-luna",
        "simple": "openai-codex/gpt-6-luna",
        "complex_unclear": "openai-codex/gpt-6-astra",
        "architecture": "openai-codex/gpt-6-astra",
        "academic": "openai-codex/gpt-6-astra",
    }.get(tier, "openai-codex/gpt-6-sol")
    other = codex_fallback if model.startswith("claude-bridge/") else "claude-bridge/claude-opus-5-5"
    return list(dict.fromkeys((model, other)))


def default_candidates(default):
    return candidates(default[0], "main")


def instructions():
    source = (ROOT / "CLAUDE.md").read_text().split("# Delegated Operational Authority", 1)[0]
    source = source.replace(
        "提示詞、文件與文章應直接陳述期望行為，避免不必要的防禦性用語。",
        "Prompts, documents, and articles state expected behavior directly.",
    )
    head = "\n".join(line for line in source.splitlines() if not line.startswith("@shared/"))
    body = (ROOT / "pi/AGENTS.md.in").read_text()
    for shared in sorted((ROOT / "shared").glob("*.md")):
        body = body.replace(f"@shared/{shared.name}", shared.read_text().rstrip())
    if "@shared/" in body:
        raise ValueError("unexpanded shared instruction import")
    strategy, default, profile_tiers, tasks = routing()
    tier_lines = [f"- Main: model `{', '.join(default_candidates(default))}`; thinking `{default[1]}`."]
    for name, (model, thinking) in profile_tiers.items():
        if name == "main":
            continue
        tier_lines.append(f"- {name}: model `{', '.join(candidates(model, name))}`; thinking `{thinking}`.")
    guidance = "For subagent dispatch, pass the selected tier's full comma-separated list as the `model` value and its thinking level as `thinking`. The `task:<category>` shorthand is available only for coding, review, recon, qa, architecture, and docs."
    return head.strip() + "\n\n" + body.rstrip() + f"\n\n## Active model strategy: {strategy}\n\n" + guidance + "\n\n" + "\n".join(tier_lines) + "\n"


def update_profile(home, state):
    agent_dir = home / ".pi/agent"
    settings_path = agent_dir / "settings.json"
    config_path = agent_dir / "herdr-agents/config.json"
    settings = read_json(settings_path)
    config = read_json(config_path)
    strategy, default, tiers, tasks = routing()
    state.setdefault("previous_settings", {key: settings.get(key) for key in FIELDS})
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


def install(home, skip_external, force):
    agent_dir = home / ".pi/agent"
    marker_path = agent_dir / ".weihung-user-claude.json"
    first_install = not marker_path.exists()
    state = read_json(marker_path)
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
        if not AAAAV.exists():
            raise ValueError(f"aaaav package is missing: {AAAAV}")
        run(["pi", "install", str(AAAAV)], home)
        run(["pi", "install", LOCAL_PACKAGE], home)
    else:
        settings = read_json(settings_path)
        settings["packages"] = [package for package in dict.fromkeys(settings.get("packages", []) + PACKAGES + [str(AAAAV), LOCAL_PACKAGE]) if not obsolete_bridge(package)]
        write_json(settings_path, settings)
    write_json(marker_path, state)


def uninstall(home, skip_external):
    agent_dir = home / ".pi/agent"
    marker_path = agent_dir / ".weihung-user-claude.json"
    if not marker_path.exists():
        return
    state = read_json(marker_path)
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
    owned = {package_id(value, agent_dir) for value in PACKAGES + [str(AAAAV), LOCAL_PACKAGE]} - previous_ids
    if not skip_external:
        installed_ids = {package_id(value, agent_dir) for value in read_json(settings_path).get("packages", [])}
        for package in PACKAGES + [str(AAAAV), LOCAL_PACKAGE]:
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
            if previous is None:
                settings.pop(key, None)
            else:
                settings[key] = previous
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
