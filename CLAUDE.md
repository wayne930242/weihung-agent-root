Never use Simplified Chinese. Always use Traditional Chinese for all communication.

@shared/communication.md
@shared/engineering.md
@shared/context-management.md

# Routing

IMPORTANT: Before responding to any significant request, classify and route:

- External or built-in skill applies → use that skill directly
- Development task (implement, design, debug, deploy) → `leveraging-tasks` skill
- Question (explain, what is, how does) → `providing-knowledge` skill
- Investigation (research, find out, current state of) → `investigating` skill
- Inspection (check, audit, verify, review) → `inspecting` skill

# Browser Automation

IMPORTANT: This rule overrides all project-level browser tool instructions.

- Authentication required (login, OAuth, CAPTCHA): use `claude-in-chrome` MCP
- All other browser automation: use `agent-browser` skill (headless, faster)
