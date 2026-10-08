"""The small managed settings: UI, terminal, panes, herdr-agents models, built-in MCP, mcp-adapter, pi-lens, open-tui, compaction."""

import hashlib
from copy import deepcopy
from pathlib import Path

from .context import Context, State
from .jsonfile import read_json, write_json
from .managed import record_keys, remember_keys, restore_keys, restore_nested, restore_value
from .paths import HERDR_MODELS, LENS_CONFIG, OPEN_TUI_CONFIG, RETIRED_ROLES_DIR
from .pins import THESIS_TOOLKIT

# pi's native compaction fires at contextWindow - reserveTokens: 500K for the 1M Opus and Sonnet, a
# ceiling for a long running turn; idle-compaction.ts compacts at 300K between turns.
OPUS_1M = "claude-bridge/claude-opus-5-5"
SONNET_1M = "claude-bridge/claude-sonnet-5-5"
COMPACTION_OVERRIDES = {OPUS_1M: {"reserveTokens": 500_000}, SONNET_1M: {"reserveTokens": 500_000}}
UI_SETTINGS = {"theme": "catppuccin-mocha", "editorPaddingX": 1, "collapseChangelog": True, "enableInstallTelemetry": False}
# install.sh puts codebase-memory-mcp in ~/.local/bin; registering it here replaces any copy imported from another
# agent's config, so its tools stay behind the `mcp` gateway instead of joining every prompt.
CODEBASE_MEMORY = "codebase-memory-mcp"
CODEBASE_MEMORY_BINARY = Path(".local/bin/codebase-memory-mcp")
MCP_SETTINGS = {"namespaceProxyTools": False}
# Global research-hub; a project .mcp.json entry of the same name (knowledge-base) takes precedence.
# Downloads use research-hub's default ~/downloads/papers.
RESEARCH_HUB = "research-hub"
RESEARCH_HUB_SERVER = {
    "command": "npx",
    "args": ["-y", THESIS_TOOLKIT, "mcp", "research-hub"],
    "env": {"RSH_LIBRARY_API_URL": "https://bib-manager-api.vercel.app", "RUST_LOG": "warn"},
}
# pi-mcp-adapter owns /mcp; pi's built-in MCP support would otherwise warn on every start that it stepped aside.
BUILTIN_MCP_OFF = "-builtin:mcp"
# These pi-lens tools stay off to keep every prompt small; `read_symbol`, `read_enclosing`, and `lens_diagnostics` cover navigation.
LENS_DISABLED_TOOLS = ("project_report", "symbol_search", "module_report")
# pi-open-tui footer segments kept off to keep the footer to what gets read; `/open-tui` still owns every other setting.
OPEN_TUI_HIDDEN_SEGMENTS = ("runtime", "cost", "extensionStatuses")


def write_or_remove(path: Path, value: dict) -> None:
    """Write what is left, or remove a file restoring emptied."""
    if value:
        write_json(path, value)
    elif path.exists():
        path.unlink()


def apply_ui(ctx: Context) -> None:
    state = ctx.state
    settings = read_json(ctx.settings_path)
    config = read_json(ctx.herdr_config_path)
    remember_keys(state, "ui_settings", settings, UI_SETTINGS)
    state.setdefault("previous_terminal", deepcopy(settings.get("terminal")))
    state.setdefault("previous_panes", deepcopy(config.get("panes")))
    settings.update(UI_SETTINGS)
    settings.setdefault("terminal", {})["showTerminalProgress"] = True
    disable_builtin_mcp(settings, state)
    config["panes"] = {**config.get("panes", {}), "mode": "split", "direction": "right"}
    write_json(ctx.settings_path, settings)
    write_json(ctx.herdr_config_path, config)
    record_keys(state, "ui_settings", settings, UI_SETTINGS)
    state["installed_terminal"] = deepcopy(settings["terminal"])
    state["installed_panes"] = deepcopy(config["panes"])


def restore_ui(ctx: Context) -> None:
    state = ctx.state
    settings = read_json(ctx.settings_path)
    restore_keys(state, "ui_settings", settings, UI_SETTINGS)
    restore_nested(settings, "terminal", state.get("installed_terminal"), state.get("previous_terminal"), ("showTerminalProgress",))
    restore_builtin_mcp(settings, state)
    write_json(ctx.settings_path, settings)
    config = read_json(ctx.herdr_config_path)
    restore_nested(config, "panes", state.get("installed_panes"), state.get("previous_panes"), ("mode", "direction"))
    write_or_remove(ctx.herdr_config_path, config)


# Marker keys the removed model strategy profile wrote; none of them is read or restored any more.
RETIRED_PROFILE_KEYS = ("installed_agent_models", "installed_models", "installed_roles", "installed_settings",
                        "installed_status", "previous_models", "previous_settings", "previous_settings_present",
                        "previous_status", "strategy")


def retire_model_profile(ctx: Context) -> None:
    """Remove the tier roles an install with the model strategy profile wrote, and its marker keys."""
    state = ctx.state
    roles_dir = ctx.home / RETIRED_ROLES_DIR
    for name, digest in state.get("installed_roles", {}).items():
        path = roles_dir / name
        if path.exists() and hashlib.sha256(path.read_bytes()).hexdigest() == digest:
            path.unlink()
    if roles_dir.exists() and not any(roles_dir.iterdir()):
        roles_dir.rmdir()
    for key in RETIRED_PROFILE_KEYS:
        state.pop(key, None)


def apply_herdr_models(ctx: Context) -> None:
    """Write pi/herdr-agents-models.json as the pi-herdr-agents `models`; a hand edit since the last install stops the run."""
    retire_model_profile(ctx)
    state = ctx.state
    config = read_json(ctx.herdr_config_path)
    desired = read_json(HERDR_MODELS)
    current = config.get("models")
    edited = current not in (None, desired, state.get("installed_herdr_models"))
    if edited and not ctx.force:
        raise ValueError(f"{ctx.herdr_config_path} `models` differs from {HERDR_MODELS}; move the change into the "
                         "repository file, or rerun with --force to replace it")
    state.setdefault("previous_herdr_models", deepcopy(current))
    config["models"] = desired
    write_json(ctx.herdr_config_path, config)
    state["installed_herdr_models"] = deepcopy(desired)


def restore_herdr_models(ctx: Context) -> None:
    state = ctx.state
    config = read_json(ctx.herdr_config_path)
    restore_value(config, "models", state.get("installed_herdr_models"), state.get("previous_herdr_models"))
    write_or_remove(ctx.herdr_config_path, config)


def disable_builtin_mcp(settings: dict, state: State) -> None:
    extensions = settings.get("extensions")
    state.setdefault("previous_extensions_present", extensions is not None)
    state.setdefault("added_builtin_mcp_off", BUILTIN_MCP_OFF not in (extensions or []))
    if BUILTIN_MCP_OFF not in (extensions or []):
        settings["extensions"] = [*(extensions or []), BUILTIN_MCP_OFF]


def restore_builtin_mcp(settings: dict, state: State) -> None:
    extensions = settings.get("extensions")
    if not state.get("added_builtin_mcp_off") or not isinstance(extensions, list):
        return
    settings["extensions"] = [item for item in extensions if item != BUILTIN_MCP_OFF]
    if not settings["extensions"] and not state.get("previous_extensions_present", True):
        settings.pop("extensions")


def mcp_config_path(agent_dir: Path) -> Path:
    """The adapter's own settings file; mcp.json stays pi's, which pi-mcp-adapter 5.0.0 also reads."""
    return agent_dir / "mcp-adapter.json"


def apply_mcp(ctx: Context) -> None:
    path = mcp_config_path(ctx.agent_dir)
    mcp = read_json(path)
    update_mcp(mcp, ctx.state, ctx.home)
    write_json(path, mcp)


def update_mcp(mcp: dict, state: State, home: Path) -> None:
    state.setdefault("previous_discovery", mcp.get("settings", {}).get("hostConfigDiscovery"))
    settings = mcp.setdefault("settings", {})
    state.setdefault("previous_mcp_settings", {key: deepcopy(settings[key]) for key in MCP_SETTINGS if key in settings})
    settings["hostConfigDiscovery"] = "on"
    settings.update(MCP_SETTINGS)
    servers = mcp.setdefault("mcpServers", {})
    state.setdefault("previous_mcp_server", deepcopy(servers.get(CODEBASE_MEMORY)))
    servers[CODEBASE_MEMORY] = {"command": str(home / CODEBASE_MEMORY_BINARY)}
    state.setdefault("previous_research_hub_server", deepcopy(servers.get(RESEARCH_HUB)))
    servers[RESEARCH_HUB] = deepcopy(RESEARCH_HUB_SERVER)
    state["installed_mcp_settings"] = dict(MCP_SETTINGS)
    state["installed_mcp_server"] = deepcopy(servers[CODEBASE_MEMORY])
    state["installed_research_hub_server"] = deepcopy(servers[RESEARCH_HUB])


def restore_mcp(ctx: Context) -> None:
    state = ctx.state
    path = mcp_config_path(ctx.agent_dir)
    mcp = read_json(path)
    if mcp.get("settings", {}).get("hostConfigDiscovery") == "on":
        previous = state.get("previous_discovery")
        if previous is None:
            mcp["settings"].pop("hostConfigDiscovery", None)
        else:
            mcp["settings"]["hostConfigDiscovery"] = previous
    restore_nested(mcp, "settings", state.get("installed_mcp_settings"), state.get("previous_mcp_settings"), tuple(MCP_SETTINGS))
    if "mcpServers" in mcp:
        restore_value(mcp["mcpServers"], CODEBASE_MEMORY, state.get("installed_mcp_server"), state.get("previous_mcp_server"))
        restore_value(mcp["mcpServers"], RESEARCH_HUB, state.get("installed_research_hub_server"), state.get("previous_research_hub_server"))
        if not mcp["mcpServers"]:
            mcp.pop("mcpServers")
    if mcp.get("settings") == {}:
        mcp.pop("settings")
    write_or_remove(path, mcp)


def apply_lens(ctx: Context) -> None:
    state = ctx.state
    path = ctx.home / LENS_CONFIG
    config = read_json(path)
    tools = config.setdefault("tools", {})
    state.setdefault("previous_lens_tools", {name: deepcopy(tools[name]) for name in LENS_DISABLED_TOOLS if name in tools})
    for name in LENS_DISABLED_TOOLS:
        tools[name] = {**tools.get(name, {}), "enabled": False}
    write_json(path, config)
    state["installed_lens_tools"] = {name: deepcopy(tools[name]) for name in LENS_DISABLED_TOOLS}


def restore_lens(ctx: Context) -> None:
    state = ctx.state
    path = ctx.home / LENS_CONFIG
    config = read_json(path)
    tools = config.get("tools")
    if not isinstance(tools, dict) or "installed_lens_tools" not in state:
        return
    previous = state.get("previous_lens_tools", {})
    for name, installed in state["installed_lens_tools"].items():
        restore_nested(tools, name, installed, previous.get(name), ("enabled",))
    if not tools:
        config.pop("tools")
    write_or_remove(path, config)


def apply_open_tui(ctx: Context) -> None:
    state = ctx.state
    path = ctx.home / OPEN_TUI_CONFIG
    config = read_json(path)
    segments = config.setdefault("footerSegments", {})
    state.setdefault("previous_open_tui_present", path.exists())
    state.setdefault("previous_open_tui_segments", {name: segments[name] for name in OPEN_TUI_HIDDEN_SEGMENTS if name in segments})
    segments.update(dict.fromkeys(OPEN_TUI_HIDDEN_SEGMENTS, False))
    write_json(path, config)
    state["installed_open_tui_segments"] = dict.fromkeys(OPEN_TUI_HIDDEN_SEGMENTS, False)


def restore_open_tui(ctx: Context) -> None:
    state = ctx.state
    path = ctx.home / OPEN_TUI_CONFIG
    config = read_json(path)
    if "installed_open_tui_segments" not in state:
        return
    restore_nested(config, "footerSegments", state["installed_open_tui_segments"],
                   state.get("previous_open_tui_segments"), OPEN_TUI_HIDDEN_SEGMENTS)
    if config or state.get("previous_open_tui_present", True):
        write_json(path, config)
    elif path.exists():
        path.unlink()


def apply_compaction(ctx: Context) -> None:
    state = ctx.state
    settings = read_json(ctx.settings_path)
    state.setdefault("previous_compaction_present", "compaction" in settings)
    compaction = settings.setdefault("compaction", {})
    state.setdefault("previous_compaction_overrides", deepcopy(compaction.get("modelOverrides")))
    compaction["modelOverrides"] = {**(compaction.get("modelOverrides") or {}), **deepcopy(COMPACTION_OVERRIDES)}
    write_json(ctx.settings_path, settings)
    state["installed_compaction_overrides"] = deepcopy(compaction["modelOverrides"])


def restore_compaction(ctx: Context) -> None:
    state = ctx.state
    settings = read_json(ctx.settings_path)
    compaction = settings.get("compaction")
    if not isinstance(compaction, dict):
        return
    restore_nested(compaction, "modelOverrides", state.get("installed_compaction_overrides"),
                   state.get("previous_compaction_overrides"), tuple(COMPACTION_OVERRIDES))
    if not compaction and not state.get("previous_compaction_present", True):
        settings.pop("compaction")
    write_json(ctx.settings_path, settings)
