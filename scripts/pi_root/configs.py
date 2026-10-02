"""The small managed settings: UI, terminal, panes, built-in MCP, mcp-adapter, pi-lens, open-tui, compaction."""

from copy import deepcopy

from .jsonfile import read_json, write_json
from .managed import remember_previous, restore_managed_keys
from .paths import LENS_CONFIG, OPEN_TUI_CONFIG
from .profile import OPUS_1M, SONNET_1M

# pi's native compaction fires at contextWindow - reserveTokens: 500K for the 1M Opus and Sonnet, a
# ceiling for a long running turn; idle-compaction.ts compacts at 300K between turns.
COMPACTION_OVERRIDES = {OPUS_1M: {"reserveTokens": 500_000}, SONNET_1M: {"reserveTokens": 500_000}}
UI_SETTINGS = {"theme": "catppuccin-mocha", "editorPaddingX": 1, "collapseChangelog": True, "enableInstallTelemetry": False}
# codebase-memory is no longer installed, but other agents' configs may still register its server;
# keeping it disabled stops pi-mcp-adapter from importing it through host config discovery.
MCP_DISABLED_SERVER = "codebase-memory-mcp"
MCP_SETTINGS = {"namespaceProxyTools": False}
# pi-mcp-adapter owns /mcp; pi's built-in MCP support would otherwise warn on every start that it stepped aside.
BUILTIN_MCP_OFF = "-builtin:mcp"
# These pi-lens tools stay off to keep every prompt small; `read_symbol`, `read_enclosing`, and `lens_diagnostics` cover navigation.
LENS_DISABLED_TOOLS = ("project_report", "symbol_search", "module_report")
# pi-open-tui footer segments kept off to keep the footer to what gets read; `/open-tui` still owns every other setting.
OPEN_TUI_HIDDEN_SEGMENTS = ("runtime", "cost", "extensionStatuses")


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
    disable_builtin_mcp(settings, state)
    config["panes"] = {**config.get("panes", {}), "mode": "split", "direction": "right"}
    write_json(settings_path, settings)
    write_json(config_path, config)
    state["installed_ui_settings"] = {key: deepcopy(settings[key]) for key in UI_SETTINGS}
    state["installed_terminal"] = deepcopy(settings["terminal"])
    state["installed_panes"] = deepcopy(config["panes"])


def disable_builtin_mcp(settings, state):
    extensions = settings.get("extensions")
    state.setdefault("previous_extensions_present", extensions is not None)
    state.setdefault("added_builtin_mcp_off", BUILTIN_MCP_OFF not in (extensions or []))
    if BUILTIN_MCP_OFF not in (extensions or []):
        settings["extensions"] = [*(extensions or []), BUILTIN_MCP_OFF]


def restore_builtin_mcp(settings, state):
    extensions = settings.get("extensions")
    if not state.get("added_builtin_mcp_off") or not isinstance(extensions, list):
        return
    settings["extensions"] = [item for item in extensions if item != BUILTIN_MCP_OFF]
    if not settings["extensions"] and not state.get("previous_extensions_present", True):
        settings.pop("extensions")


def mcp_config_path(agent_dir):
    """The adapter's own settings file; mcp.json stays pi's, which pi-mcp-adapter 5.0.0 also reads."""
    return agent_dir / "mcp-adapter.json"


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


def update_open_tui(home, state):
    path = home / OPEN_TUI_CONFIG
    config = read_json(path)
    segments = config.setdefault("footerSegments", {})
    state.setdefault("previous_open_tui_present", path.exists())
    state.setdefault("previous_open_tui_segments", {name: segments[name] for name in OPEN_TUI_HIDDEN_SEGMENTS if name in segments})
    segments.update(dict.fromkeys(OPEN_TUI_HIDDEN_SEGMENTS, False))
    write_json(path, config)
    state["installed_open_tui_segments"] = dict.fromkeys(OPEN_TUI_HIDDEN_SEGMENTS, False)


def restore_open_tui(home, state):
    path = home / OPEN_TUI_CONFIG
    config = read_json(path)
    if "installed_open_tui_segments" not in state:
        return
    restore_managed_keys(config, "footerSegments", state["installed_open_tui_segments"],
                         state.get("previous_open_tui_segments"), OPEN_TUI_HIDDEN_SEGMENTS)
    if config or state.get("previous_open_tui_present", True):
        write_json(path, config)
    elif path.exists():
        path.unlink()


def update_compaction(home, state):
    settings_path = home / ".pi/agent/settings.json"
    settings = read_json(settings_path)
    state.setdefault("previous_compaction_present", "compaction" in settings)
    compaction = settings.setdefault("compaction", {})
    state.setdefault("previous_compaction_overrides", deepcopy(compaction.get("modelOverrides")))
    compaction["modelOverrides"] = {**(compaction.get("modelOverrides") or {}), **deepcopy(COMPACTION_OVERRIDES)}
    write_json(settings_path, settings)
    state["installed_compaction_overrides"] = deepcopy(compaction["modelOverrides"])


def restore_compaction(settings, state):
    compaction = settings.get("compaction")
    if not isinstance(compaction, dict):
        return
    restore_managed_keys(compaction, "modelOverrides", state.get("installed_compaction_overrides"),
                         state.get("previous_compaction_overrides"), tuple(COMPACTION_OVERRIDES))
    if not compaction and not state.get("previous_compaction_present", True):
        settings.pop("compaction")
