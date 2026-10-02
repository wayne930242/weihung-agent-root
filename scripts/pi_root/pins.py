"""Every pinned package source; `scripts/pi-pins.py` rewrites the versions in this file, so it imports nothing."""

BRIDGE_SOURCE = "git:github.com/wayne930242/pi-claude-bridge@b2735123eb51862136667b5f829ce1343bb7f93b"
# Fork branch of upstream PR latentminds-ai/pi-quotas#51 (claude-bridge support); switch to
# npm:@latentminds/pi-quotas once released.
QUOTAS_SOURCE = "git:github.com/wayne930242/pi-quotas@caa30da4f6d3d3e2a57edbb85e8de1f856f7ee6b"
WEB_ACCESS_SOURCE = "npm:pi-web-access@0.35.0"
CLAUDE_RULES_SOURCE = "npm:pi-code@1.4.1"
# Straw Boss owns the Pi dispatch workflow: its skills, dispatch_control, and pane balancing.
STRAW_BOSS_SOURCE = "git:github.com/wayne930242/straw-boss@9de8a707a118b4936474c888325bfb2af25a9841"
# Every other revision of a pinned git package, including an unpinned spec, is retired for the current pin.
PINNED_GIT = {
    BRIDGE_SOURCE: ("git:github.com/wayne930242/pi-claude-bridge@",),
    STRAW_BOSS_SOURCE: ("git:github.com/wayne930242/straw-boss",),
    QUOTAS_SOURCE: ("git:github.com/wayne930242/pi-quotas",),
}
# Versioned specs keep every machine on the same release; `pi update` skips them, so bump them here.
# The theme collection loads only Catppuccin Mocha, which matches the Herdr theme, and none of its skills.
THEME_PACKAGE = {"source": "npm:@victor-software-house/pi-curated-themes@0.2.1", "themes": ["themes/catppuccin-mocha.json"], "skills": []}
# pi-code loads only claude-rules.ts, which reads each project's .claude/rules as Claude Code does;
# its other extensions duplicate the todo, MCP, subagent, and web packages below.
CLAUDE_RULES_PACKAGE = {"source": CLAUDE_RULES_SOURCE, "extensions": ["extensions/claude-rules.ts"]}
HERDR_AGENTS_SOURCE = "npm:pi-herdr-agents@2.0.4"
PACKAGES = [
    BRIDGE_SOURCE,
    HERDR_AGENTS_SOURCE,
    STRAW_BOSS_SOURCE,
    "npm:pi-mcp-adapter@5.0.0",
    "npm:pi-intercom@0.16.0",
    "npm:pi-ask-user@0.15.1",
    "npm:@juicesharp/rpiv-todo@2.12.0",
    THEME_PACKAGE,
    "npm:pi-open-tui@0.3.10",
    WEB_ACCESS_SOURCE,
    "npm:pi-lens@4.3.0",
    QUOTAS_SOURCE,
    "npm:@moyai/pi-session-hoarder@0.2.0",
    "npm:pi-jev-compaction@1.0.0",
    "npm:cc-safety-net@2.5.0",
    "npm:pi-codex-image-gen@0.1.13",
    "npm:pi-secret-drop@0.1.6",
    "npm:pi-robot-hand@0.1.1",
    "npm:@pify/memory@0.13.1",
    "npm:pi-loop-monitor@0.2.1",
    "npm:@narumitw/pi-goal@0.54.8",
    "npm:pi-phoenix-otel@0.2.0",
    CLAUDE_RULES_PACKAGE,
]
# The Playwriter CLI drives the user's own Chrome through its extension; playwriter-relay.ts starts its relay.
PLAYWRITER = "playwriter@0.7.0"
# thesis-toolkit launches the research-hub MCP server (literature search, open-access download, bibliography saves).
THESIS_TOOLKIT = "thesis-toolkit@0.1.2"
AAAAV_GIT = "git:github.com/wayne930242/aaaav"
