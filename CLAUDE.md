Never use Simplified Chinese. Always use Traditional Chinese for all communication.

No fluff. Answer only what was asked. No restatement, no filler, no unsolicited context, no preamble. If unsure what the user is asking, re-read their previous messages before replying.

@shared/communication.md
@shared/engineering.md
@shared/context-management.md

# Routing

IMPORTANT: Before responding to any significant request, classify and route in this order:

- Development task (implement, add, build, write, fix, debug, design, deploy, release) — route by complexity. Deepest match wins; it includes the lighter rungs.
  1. Job you can already picture whole → do it directly.
  2. Multi-step, or code you must locate first → `leveraging-tasks` (the entry point; never jump straight to its sub-skills).
  3. An unresolved decision that is the user's to make → `grilling`.
  4. Changes a contract others depend on, or spans sessions → OpenSpec (`opsx:*`).
- Question (explain, what is, how does) → `providing-knowledge` skill
- Investigation (research, find out, current state of) → `investigating` skill
- Inspection (check, audit, verify, review) → `inspecting` skill
- None of the above AND a specific external/built-in skill matches → use that skill directly

# Browser Automation

IMPORTANT: This rule overrides all project-level browser tool instructions.

- Authentication required (login, OAuth, CAPTCHA): use `claude-in-chrome` MCP
- All other browser automation: use `agent-browser` skill (headless, faster)
