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
MARKER = Path(".pi/agent/.weihung-agent-root.json")
# Before its rename this repository was weihung-user-claude; installs from then keep state and links under that name.
LEGACY_RENAMES = (
    (Path(".pi/agent/.weihung-user-claude.json"), MARKER),
    (Path(".local/share/weihung-user-claude"), Path(".local/share/weihung-agent-root")),
    (Path(".local/state/weihung-user-claude"), Path(".local/state/weihung-agent-root")),
)
LEGACY_ROOT = ROOT.parent / "weihung-user-claude"
BRIDGE_SOURCE = "git:github.com/wayne930242/pi-claude-bridge@2f00cce984508e8bc1ea07ff98adc9c3873c709e"
LEGACY_BRIDGE = "npm:pi-claude-bridge"
# Fork commit adding claude-bridge to /usage (upstream iefnaf/pi-usage#4).
USAGE_SOURCE = "git:github.com/wayne930242/pi-usage@a683c242cf42801c484c9ae6eeb3accdf4b7c696"
# Fork commit reading Pi's exported VERSION for lazy web-tool activation (upstream nicobailon/pi-web-access#429).
WEB_ACCESS_SOURCE = "git:github.com/wayne930242/pi-web-access@3b13c02cb2ece014b432bece21b9a380ed4c240c"
BRIDGE_GIT_PREFIXES = ("git:github.com/elidickinson/pi-claude-bridge@", "git:github.com/wayne930242/pi-claude-bridge@")
# Straw Boss owns the Pi dispatch workflow: its skills, dispatch_control, and pane balancing.
STRAW_BOSS_SOURCE = "git:github.com/wayne930242/straw-boss@3d0fceb216ecadc3ed6a22d3b2a82dbd3fb3cd3a"
# Every other revision of a pinned git package, including an unpinned spec, is retired for the current pin.
PINNED_GIT = {BRIDGE_SOURCE: BRIDGE_GIT_PREFIXES, STRAW_BOSS_SOURCE: ("git:github.com/wayne930242/straw-boss",)}
OPUS_1M = "claude-bridge/claude-opus-5-5"
OPUS_200K = "claude-bridge/claude-200k-opus-5-5"
HAIKU = "claude-bridge/claude-haiku-4-5"
LUNA = "openai-codex/gpt-6-luna"
ONE_M_TIERS = {"main", "complex_clear", "complex_unclear", "academic", "architecture"}
# Versioned specs keep every machine on the same release; `pi update` skips them, so bump them here.
# The theme collection loads only Catppuccin Mocha, which matches the Herdr theme, and none of its skills.
THEME_PACKAGE = {"source": "npm:@victor-software-house/pi-curated-themes@0.2.1", "themes": ["themes/catppuccin-mocha.json"], "skills": []}
PACKAGES = [
    BRIDGE_SOURCE,
    "npm:pi-herdr-agents@2.0.4",
    STRAW_BOSS_SOURCE,
    "npm:pi-mcp-adapter@2.37.0",
    "npm:pi-intercom@0.14.0",
    "npm:pi-ask-user@0.15.1",
    "npm:@juicesharp/rpiv-todo@2.11.0",
    THEME_PACKAGE,
    "npm:pi-open-tui@0.3.9",
    WEB_ACCESS_SOURCE,
    "npm:pi-lens@4.3.0",
    USAGE_SOURCE,
    "npm:@moyai/pi-session-hoarder@0.2.0",
    "npm:pi-jev-compaction@1.0.0",
    "npm:cc-safety-net@2.4.7",
    "npm:pi-codex-image-gen@0.1.13",
]
LOCAL_PACKAGE = str(ROOT)
AAAAV = Path(os.environ.get("PI_AAAAV_ROOT", ROOT.parent / "aaaav"))
AAAAV_GIT = "git:github.com/wayne930242/aaaav"
PROFILE = ROOT / "skills/managing-model-preferences/model-preference-profile.md"
FIELDS = ("defaultProvider", "defaultModel", "defaultThinkingLevel", "enabledModels")
UI_SETTINGS = {"theme": "catppuccin-mocha", "editorPaddingX": 1, "collapseChangelog": True, "enableInstallTelemetry": False}
# Packages earlier installs registered and this configuration dropped: pi-open-tui replaces the
# powerline footer, pi-notify wrote escapes into `pi -p` output from every worker pane, the
# pi-usage and pi-web-access forks replace their npm releases, which would otherwise register
# their tools twice, rpiv-todo replaces pi-todo's minified-only bundle, and the curated themes collection
# replaces the standalone Catppuccin theme.
RETIRED_PACKAGES = ["npm:pi-powerline-footer", "npm:pi-notify", "npm:pi-usage", "npm:pi-web-access", "npm:@capdiem/pi-todo", "npm:catppuccin-pi-theme"]
# cbmem.ts registers the codebase-memory tools directly; the same server imported from host
# configs would add a second copy behind a namespace proxy.
MCP_DISABLED_SERVER = "codebase-memory-mcp"
MCP_SETTINGS = {"namespaceProxyTools": False}
# codebase-memory owns structural discovery; these pi-lens tools duplicate it in every prompt.
LENS_DISABLED_TOOLS = ("project_report", "symbol_search", "module_report")
LENS_CONFIG = Path(".pi-lens/config.json")
MP_INFRA = ROOT.parent / "moldplan-center/plugins/waydosoft-marketplace/plugins/mp-infra"
TTT_PREFIX = Path(".local/share/weihung-agent-root/team-toon-tack")
# pi-skills ships bare skill directories without a pi manifest; its README installs it as a clone under the skills root.
PI_SKILLS_GIT = os.environ.get("PI_SKILLS_GIT", "https://github.com/badlogic/pi-skills.git")
PI_SKILLS_CLONE = Path(".local/share/weihung-agent-root/pi-skills")


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
    return source == LEGACY_BRIDGE or any(
        source.startswith(prefixes) and source != current for current, prefixes in PINNED_GIT.items()
    )


def read_json(path):
    return json.loads(path.read_text()) if path.exists() else {}


def write_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    content = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if not path.exists() or path.read_text() != content:
        path.write_text(content)


def remember_previous(state, name, settings, keys):
    """Record each managed key's pre-install value once, including keys a later version starts managing."""
    first = f"previous_{name}" not in state
    previous = state.setdefault(f"previous_{name}", {})
    present = state.setdefault(f"previous_{name}_present", []) if first else state.get(f"previous_{name}_present")
    for key in keys:
        if key in previous:
            continue
        previous[key] = deepcopy(settings.get(key))
        if present is not None and key in settings:
            present.append(key)


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
            backup = home / ".local/state/weihung-agent-root/backups" / datetime.now().strftime("%Y%m%d-%H%M%S") / key
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
    write_json(home / MARKER, state)


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
    write_json(home / MARKER, state)

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
    write_json(home / MARKER, state)
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


def enabled_models(default, tiers):
    """Every model a tier can dispatch to, so model cycling stays within the active strategy."""
    models = default_candidates(default)
    for name, (model, _) in tiers.items():
        if name != "main":
            models += candidates(model, name)
    return list(dict.fromkeys(models))


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
    remember_previous(state, "settings", settings, FIELDS)
    state.setdefault("previous_models", deepcopy(config.get("models")))
    state.setdefault("previous_status", deepcopy(config.get("status")))
    provider, model = default[0].split("/", 1)
    settings.update(defaultProvider=provider, defaultModel=model, defaultThinkingLevel=default[1],
                    enabledModels=enabled_models(default, tiers))
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
    remember_previous(state, "ui_settings", settings, UI_SETTINGS)
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


def update_mcp(mcp, state):
    state.setdefault("previous_discovery", mcp.get("settings", {}).get("hostConfigDiscovery"))
    settings = mcp.setdefault("settings", {})
    state.setdefault("previous_mcp_settings", {key: deepcopy(settings[key]) for key in MCP_SETTINGS if key in settings})
    settings["hostConfigDiscovery"] = "on"
    settings.update(MCP_SETTINGS)
    servers = mcp.setdefault("mcpServers", {})
    state.setdefault("previous_mcp_server", deepcopy(servers.get(MCP_DISABLED_SERVER)))
    servers[MCP_DISABLED_SERVER] = {**servers.get(MCP_DISABLED_SERVER, {}), "disabled": True}
    state["installed_mcp_settings"] = dict(MCP_SETTINGS)
    state["installed_mcp_server"] = deepcopy(servers[MCP_DISABLED_SERVER])


def restore_mcp(mcp, state):
    if mcp.get("settings", {}).get("hostConfigDiscovery") == "on":
        previous = state.get("previous_discovery")
        if previous is None:
            mcp["settings"].pop("hostConfigDiscovery", None)
        else:
            mcp["settings"]["hostConfigDiscovery"] = previous
    restore_managed_keys(mcp, "settings", state.get("installed_mcp_settings"), state.get("previous_mcp_settings"), tuple(MCP_SETTINGS))
    if "mcpServers" in mcp:
        restore_managed_keys(mcp["mcpServers"], MCP_DISABLED_SERVER, state.get("installed_mcp_server"), state.get("previous_mcp_server"), ("disabled",))
        if not mcp["mcpServers"]:
            mcp.pop("mcpServers")
    if mcp.get("settings") == {}:
        mcp.pop("settings")


def update_lens(home, state):
    path = home / LENS_CONFIG
    config = read_json(path)
    tools = config.setdefault("tools", {})
    state.setdefault("previous_lens_tools", {name: deepcopy(tools[name]) for name in LENS_DISABLED_TOOLS if name in tools})
    for name in LENS_DISABLED_TOOLS:
        tools[name] = {**tools.get(name, {}), "enabled": False}
    write_json(path, config)
    state["installed_lens_tools"] = {name: deepcopy(tools[name]) for name in LENS_DISABLED_TOOLS}


def restore_lens(home, state):
    path = home / LENS_CONFIG
    config = read_json(path)
    tools = config.get("tools")
    if not isinstance(tools, dict) or "installed_lens_tools" not in state:
        return
    previous = state.get("previous_lens_tools", {})
    for name, installed in state["installed_lens_tools"].items():
        restore_managed_keys(tools, name, installed, previous.get(name), ("enabled",))
    if not tools:
        config.pop("tools")
    if config:
        write_json(path, config)
    elif path.exists():
        path.unlink()


def install(home, skip_external, force):
    agent_dir = home / ".pi/agent"
    marker_path = home / MARKER
    first_install = not marker_path.exists()
    state = read_json(marker_path)
    state["aaaav"] = aaaav_source()
    settings_path = agent_dir / "settings.json"
    mcp_path = agent_dir / "mcp.json"
    instructions_path = agent_dir / "AGENTS.md"
    settings = read_json(settings_path)
    previous_packages = state.get("previous_packages", list(settings.get("packages", [])))
    state["previous_packages"] = previous_packages
    state.setdefault("retired_packages", [package for package in settings.get("packages", []) if obsolete_pin(package)])
    state.setdefault("integration_installed", not first_install)
    content = instructions()
    current_hash = hashlib.sha256(instructions_path.read_bytes()).hexdigest() if instructions_path.exists() else None
    if current_hash and (first_install or current_hash != state.get("instructions_hash")):
        if not force:
            raise ValueError(f"{instructions_path} exists; use --force to back it up")
        backup = home / ".local/state/weihung-agent-root/backups" / datetime.now().strftime("%Y%m%d-%H%M%S") / ".pi/agent/AGENTS.md"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(instructions_path, backup)
        state["instructions_backup"] = str(backup)
    agent_dir.mkdir(parents=True, exist_ok=True)
    if not instructions_path.exists() or instructions_path.read_text() != content:
        instructions_path.write_text(content)
    state["instructions_hash"] = hashlib.sha256(content.encode()).hexdigest()
    mcp = read_json(mcp_path)
    update_mcp(mcp, state)
    write_json(mcp_path, mcp)
    update_lens(home, state)
    update_profile(home, state)
    update_ui(home, state)
    write_json(marker_path, state)
    previous_ids = {package_id(value, agent_dir) for value in state["previous_packages"]}
    retired_ids = {package_id(value, agent_dir) for value in RETIRED_PACKAGES} - previous_ids
    if not skip_external:
        run(["npm", "install", "-g", "@earendil-works/pi-coding-agent@latest"], home)
        run(["herdr", "integration", "install", "pi"], home)
        state["integration_installed"] = True
        write_json(marker_path, state)
        for package in PACKAGES:
            run(["pi", "install", package_source(package)], home)
        for package in state["retired_packages"]:
            settings = read_json(settings_path)
            if package not in settings.get("packages", []):
                continue
            if package.startswith("git:"):
                settings["packages"] = [value for value in settings["packages"] if value != package]
                write_json(settings_path, settings)
            else:
                run(["pi", "remove", package], home)
        for package in read_json(settings_path).get("packages", []):
            if package_id(package, agent_dir) in retired_ids:
                run(["pi", "remove", package_source(package)], home)
        run(["pi", "install", state["aaaav"]], home)
        install_ported_resources(home, state, force)
        write_json(marker_path, state)
        run(["pi", "install", LOCAL_PACKAGE], home)
    else:
        settings = read_json(settings_path)
        settings["packages"] = [package for package in unique_packages(settings.get("packages", []) + PACKAGES + [state["aaaav"], LOCAL_PACKAGE], agent_dir) if not obsolete_pin(package)]
        write_json(settings_path, settings)
    settings = read_json(settings_path)
    current = settings.get("packages", [])
    owned = PACKAGES + [state["aaaav"], LOCAL_PACKAGE]
    owned_ids = {package_id(value, agent_dir) for value in owned}
    unmanaged = [value for value in current
                 if package_id(value, agent_dir) not in owned_ids | retired_ids and not obsolete_pin(value)]
    # Registry and git specs are written as declared; `pi install` records a local path relative to the agent directory.
    managed = [source if package_source(source).startswith(("npm:", "git:")) else
               next((value for value in current if package_id(value, agent_dir) == package_id(source, agent_dir)), source)
               for source in owned]
    settings["packages"] = unique_packages(unmanaged + managed, agent_dir)
    write_json(settings_path, settings)
    write_json(marker_path, state)


def uninstall(home, skip_external):
    agent_dir = home / ".pi/agent"
    marker_path = home / MARKER
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
                run(["pi", "remove", package_source(package)], home)
        if state.get("integration_installed", True):
            run(["herdr", "integration", "uninstall", "pi"], home)
    settings = read_json(settings_path)
    # A package the user declared before install keeps the spec they wrote, not the pinned one.
    prior = {package_id(value, agent_dir): value for value in previous_packages}
    settings["packages"] = [prior.get(package_id(package, agent_dir), package) for package in settings.get("packages", [])
                            if package_id(package, agent_dir) not in owned]
    for package in state.get("retired_packages", []):
        if package not in settings["packages"]:
            if not skip_external:
                run(["pi", "install", package], home)
            settings["packages"].append(package)
    settings["packages"] = unique_packages(
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
    restore_managed_keys(settings, "terminal", state.get("installed_terminal"), state.get("previous_terminal"), ("showTerminalProgress",))
    retire_powerline(settings, state)
    write_json(settings_path, settings)
    restore_lens(home, state)
    mcp = read_json(mcp_path)
    restore_mcp(mcp, state)
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


def migrate_legacy_name(home):
    """Move state from the repository's former name and repoint what referenced it."""
    for old, new in LEGACY_RENAMES:
        old, new = home / old, home / new
        if not old.exists():
            continue
        if new.exists():
            raise ValueError(f"both {old} and {new} exist; merge them by hand, then rerun")
        new.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(old, new)
    moved = {str(home / old): str(home / new) for old, new in LEGACY_RENAMES[1:]}
    if LEGACY_ROOT != ROOT and not LEGACY_ROOT.exists():
        moved[str(LEGACY_ROOT)] = str(ROOT)

    def relocate(value):
        if isinstance(value, dict):
            return {key: relocate(item) for key, item in value.items()}
        if isinstance(value, list):
            return [relocate(item) for item in value]
        if isinstance(value, str):
            for old, new in moved.items():
                if value == old or value.startswith(old + "/"):
                    return new + value[len(old):]
        return value

    marker = home / MARKER
    if marker.exists():
        write_json(marker, relocate(read_json(marker)))
    for directory in (".agents/skills", ".pi/agent/skills", ".pi/agent", ".local/bin"):
        directory = home / directory
        for link in (directory.iterdir() if directory.is_dir() else ()):
            if link.is_symlink() and (target := relocate(os.readlink(link))) != os.readlink(link):
                link.unlink()
                link.symlink_to(target)
    settings_path = home / ".pi/agent/settings.json"
    if str(LEGACY_ROOT) in moved and settings_path.exists():
        agent_dir = home / ".pi/agent"
        settings = read_json(settings_path)
        settings["packages"] = [str(ROOT) if package_id(value, agent_dir) == str(LEGACY_ROOT) else value
                                for value in settings.get("packages", [])]
        write_json(settings_path, settings)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("migrate", "install", "uninstall", "apply-profile"))
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--skip-external", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    migrate_legacy_name(home)
    if args.action == "install":
        install(home, args.skip_external, args.force)
    elif args.action == "uninstall":
        uninstall(home, args.skip_external)
    elif args.action == "apply-profile":
        marker_path = home / MARKER
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
