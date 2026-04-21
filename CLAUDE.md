Never use Simplified Chinese. Always use Traditional Chinese for all communication.

No fluff. Answer only what was asked. No restatement, no filler, no unsolicited context, no preamble. If unsure what the user is asking, re-read their previous messages before replying.

@shared/communication.md
@shared/engineering.md
@shared/context-management.md

# Routing

IMPORTANT: Before responding to any significant request, classify and route in this order:

- Development task (implement, add, build, write, fix, debug, design, deploy, release) → `leveraging-tasks` skill FIRST. It delegates to sub-skills (including external ones like `superpowers:*`) internally — do not bypass it.
- Question (explain, what is, how does) → `providing-knowledge` skill
- Investigation (research, find out, current state of) → `investigating` skill
- Inspection (check, audit, verify, review) → `inspecting` skill
- None of the above AND a specific external/built-in skill matches → use that skill directly

# Browser Automation

IMPORTANT: This rule overrides all project-level browser tool instructions.

- Authentication required (login, OAuth, CAPTCHA): use `claude-in-chrome` MCP
- All other browser automation: use `agent-browser` skill (headless, faster)

@RTK.md
