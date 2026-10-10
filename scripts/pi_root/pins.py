"""Every pinned package source; `scripts/pi-pins.py` rewrites the versions in this file, so it imports nothing."""

BRIDGE_SOURCE = "git:github.com/wayne930242/pi-claude-bridge@166d49e97bc3c298ed7f9c3aefa9c8c54d36bae5"
# Fork branch of upstream PR latentminds-ai/pi-quotas#51 (claude-bridge support); switch to
# npm:@latentminds/pi-quotas once released.
QUOTAS_SOURCE = "git:github.com/wayne930242/pi-quotas@caa30da4f6d3d3e2a57edbb85e8de1f856f7ee6b"
WEB_ACCESS_SOURCE = "npm:pi-web-access@0.35.0"
CLAUDE_RULES_SOURCE = "npm:pi-code@1.4.1"
# Straw Boss owns the Pi dispatch workflow: its skills, dispatch_control, and pane balancing.
STRAW_BOSS_SOURCE = "git:github.com/wayne930242/straw-boss@136341444b51305bab4581380c68280050ff24b6"
# Fork pin of giuseppecrj/pi-herdr-agents: upstream v3.2.0 plus PR #84 (branch weihung/v3-integration).
# Once upstream releases #84, return to the npm release: set this to npm:pi-herdr-agents@<version>, drop the PINNED_GIT
# entry and the FORK_BRANCHES entry in scripts/pi-pins.py, and move "npm:pi-herdr-agents" out of RETIRED_SOURCES.
HERDR_AGENTS_SOURCE = "git:github.com/wayne930242/pi-herdr-agents@1616f37ab270b22caefd8cccb1f7bc3f793e67b2"
# The pi-herdr-agents v3 role pack: planner, /plan, and /skill:plan. Its orchestrate skill is filtered out because
# skills/orchestrate owns our trimmed version. Pinned by hand (MANUAL_PINS) since a 0.x bump can change the planner.
HERDR_ROLES_SOURCE = "npm:pi-herdr-roles@0.1.0"
HERDR_ROLES_PACKAGE = {"source": HERDR_ROLES_SOURCE, "skills": ["!orchestrate"]}
# Every other revision of a pinned git package, including an unpinned spec, is retired for the current pin.
PINNED_GIT = {
    BRIDGE_SOURCE: ("git:github.com/wayne930242/pi-claude-bridge@",),
    STRAW_BOSS_SOURCE: ("git:github.com/wayne930242/straw-boss",),
    QUOTAS_SOURCE: ("git:github.com/wayne930242/pi-quotas",),
    HERDR_AGENTS_SOURCE: ("git:github.com/wayne930242/pi-herdr-agents",),
}
# Versioned specs keep every machine on the same release; `pi update` skips them, so bump them here.
# Catppuccin Mocha with only official palette colors, matching Herdr, Ghostty, and SketchyBar; the filter loads Mocha alone.
THEME_PACKAGE = {"source": "npm:@sherif-fanous/pi-catppuccin@0.2.0", "themes": ["themes/catppuccin-mocha.json"]}
# Registry packages this setup installed before and now drops; install removes them from settings.
# pi-curated-themes shipped a catppuccin-mocha with off-palette accents; pi-secret-drop is now part of pi-robot-hand;
# the npm pi-herdr-agents release is replaced by the fork pin above, and pi must never load both.
RETIRED_SOURCES = ("npm:@victor-software-house/pi-curated-themes", "npm:pi-secret-drop", "npm:pi-herdr-agents")
# pi-code loads only claude-rules.ts, which reads each project's .claude/rules as Claude Code does;
# its other extensions duplicate the todo, MCP, subagent, and web packages below.
CLAUDE_RULES_PACKAGE = {"source": CLAUDE_RULES_SOURCE, "extensions": ["extensions/claude-rules.ts"]}
PACKAGES = [
    BRIDGE_SOURCE,
    HERDR_AGENTS_SOURCE,
    HERDR_ROLES_PACKAGE,
    STRAW_BOSS_SOURCE,
    "npm:pi-mcp-adapter@5.0.0",
    "npm:pi-intercom@0.16.0",
    "npm:pi-ask-user@0.16.0",
    "npm:@juicesharp/rpiv-todo@2.12.0",
    THEME_PACKAGE,
    "npm:pi-open-tui@0.3.11",
    WEB_ACCESS_SOURCE,
    "npm:pi-lens@4.3.0",
    QUOTAS_SOURCE,
    "npm:@moyai/pi-session-hoarder@0.2.0",
    "npm:pi-jev-compaction@1.0.0",
    "npm:cc-safety-net@2.5.2",
    "npm:pi-codex-image-gen@0.1.15",
    "npm:pi-robot-hand@0.2.2",
    "npm:@pify/memory@0.13.1",
    "npm:pi-loop-monitor@0.2.1",
    "npm:@narumitw/pi-goal@0.54.8",
    "npm:pi-phoenix-otel@0.2.0",
    CLAUDE_RULES_PACKAGE,
]
# The Playwriter CLI drives the user's own Chrome through its extension; playwriter-relay.ts starts its relay.
PLAYWRITER = "playwriter@0.7.0"
# thesis-toolkit launches the research-hub MCP server (literature search, open-access download, bibliography saves).
THESIS_TOOLKIT = "thesis-toolkit@0.1.3"
AAAAV_GIT = "git:github.com/wayne930242/aaaav"
