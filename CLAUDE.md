Never use Simplified Chinese. Always use Traditional Chinese for all communication.

No fluff. Answer only what was asked. No restatement, no filler, no unsolicited context, no preamble. If unsure what the user is asking, re-read their previous messages before replying.

@shared/communication.md
@shared/engineering.md
@shared/context-management.md

# Delegated Operational Authority

IMPORTANT: The "ask when uncertain" / "present, don't pick silently" defaults in `shared/communication.md` and `shared/engineering.md` are about genuine ambiguity — an architecture choice, an unclear scope, a judgment call that's actually mine to make. They do not apply to a decision a skill or role you're operating under has already delegated to you — e.g. an orchestrator/main-agent role instructed to decide and state a dispatch or coordination call, not ask. Follow that skill's own delegation there: state the decision and act, don't re-ask me.

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

# Cross-Model Consult

Codex participates through `/codex:rescue`.

- Generating an asset (fixtures, scaffolds, sample data, boilerplate) → delegate, then verify the output yourself
- Generating an image → delegate, and state that the asset is project-bound, or it stays under `$CODEX_HOME/generated_images/`
- Reviewing a document (spec, plan, docs — not code) → read-only; findings get judged, not adopted
- A significant decision → read-only, for perspective; Codex informs, it never decides
- Translation, formatting, extraction — mechanical single-shot tasks → route with `--model gpt-5.6-luna --effort low`
- Deep/adversarial review, high-stakes debugging → route with `--effort high` (leave model unset)

# Browser Automation

IMPORTANT: This rule overrides all project-level browser tool instructions.

- Authentication required (login, OAuth, CAPTCHA): use `claude-in-chrome` MCP
- All other browser automation: use `agent-browser` skill (headless, faster)
