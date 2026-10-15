"""Every pinned package source; `scripts/pi-pins.py` rewrites the versions in this file, so it imports nothing."""

BRIDGE_SOURCE = "git:github.com/wayne930242/pi-claude-bridge@923c16c0fc6e61bcf27d6e5ba3e5ba0ae37d0062"
# Fork branch of upstream PR latentminds-ai/pi-quotas#51 (claude-bridge support); switch to
# npm:@latentminds/pi-quotas once released.
QUOTAS_SOURCE = "git:github.com/wayne930242/pi-quotas@caa30da4f6d3d3e2a57edbb85e8de1f856f7ee6b"
WEB_ACCESS_SOURCE = "npm:pi-web-access@0.41.0"
CLAUDE_RULES_SOURCE = "npm:pi-code@1.5.2"
# Straw Boss owns the Pi dispatch workflow: its skills, dispatch_control, and pane balancing.
STRAW_BOSS_SOURCE = "git:github.com/wayne930242/straw-boss@d6d64addc56cdd0a2af2717289bfa6ea4d15f70f"
# Fork pin of giuseppecrj/pi-herdr-agents: upstream v3.2.0 plus PRs #84 and #87 (branch weihung/v3-integration).
# Once upstream releases both, return to the npm release: set this to npm:pi-herdr-agents@<version>, drop the PINNED_GIT
# entry and the FORK_BRANCHES entry in scripts/pi-pins.py, and move "npm:pi-herdr-agents" out of RETIRED_SOURCES.
HERDR_AGENTS_SOURCE = "git:github.com/wayne930242/pi-herdr-agents@ac809ab26c999f7e4e97db82746b8468ad2dadf9"
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
THEME_PACKAGE = {"source": "npm:@sherif-fanous/pi-catppuccin@0.3.0", "themes": ["themes/catppuccin-mocha.json"]}
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
    "npm:pi-mcp-adapter@5.3.0",
    "npm:pi-intercom@0.17.1",
    "npm:pi-ask-user@0.16.0",
    "npm:@juicesharp/rpiv-todo@2.13.8",
    THEME_PACKAGE,
    "npm:pi-open-tui@0.3.11",
    WEB_ACCESS_SOURCE,
    "npm:pi-lens@4.4.3",
    QUOTAS_SOURCE,
    "npm:@moyai/pi-session-hoarder@0.2.0",
    "npm:pi-jev-compaction@1.0.0",
    "npm:cc-safety-net@2.6.12",
    "npm:pi-codex-image-gen@0.2.0",
    "npm:pi-robot-hand@0.2.2",
    "npm:pi-auto-tab-name@0.2.0",
    "npm:@pify/memory@0.14.0",
    "npm:pi-loop-monitor@0.2.5",
    "npm:@narumitw/pi-goal@0.54.11",
    "npm:pi-phoenix-otel@0.2.0",
    # Antigravity (agy) Google login: /login antigravity, plus the google_search and generate_image tools.
    "npm:pi-antigravity@0.10.0",
    CLAUDE_RULES_PACKAGE,
]
# The Playwriter CLI drives the user's own Chrome through its extension; playwriter-relay.ts starts its relay.
PLAYWRITER = "playwriter@0.8.0"
# thesis-toolkit launches the research-hub MCP server (literature search, open-access download, bibliography saves).
THESIS_TOOLKIT = "thesis-toolkit@0.1.3"
AAAAV_GIT = "git:github.com/wayne930242/aaaav"
