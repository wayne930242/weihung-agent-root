Never use Simplified Chinese. Always use Traditional Chinese for all communication.

No fluff. Answer only what was asked. No restatement, no filler, no unsolicited context, no preamble. If unsure what the user is asking, re-read their previous messages before replying.

@shared/communication.md
@shared/engineering.md
@shared/context-management.md

# Delegated Operational Authority

IMPORTANT: The "ask when uncertain" / "present, don't pick silently" defaults in `shared/communication.md` and `shared/engineering.md` are about genuine ambiguity — an architecture choice, an unclear scope, a judgment call that's actually mine to make. They do not apply to a decision a skill or role you're operating under has already delegated to you — e.g. an orchestrator/main-agent role instructed to decide and state a dispatch or coordination call, not ask. Follow that skill's own delegation there: state the decision and act, don't re-ask me.

# Routing

IMPORTANT: Before responding to a significant request, choose one owner:

- A named or exact specialized skill → use it.
- Explanation or comparison → `providing-knowledge`.
- Research → `investigating`.
- Check, audit, or review → `inspecting`.
- Any source-changing work → `leveraging-tasks`.
- A user-owned unresolved decision → `grilling`.

Specialized skills return source-changing work to `leveraging-tasks`. Entering
that owner does not require SDD files: clear local work with little future reuse
stays inline, while durable decisions and coordination leave phased artifacts
under `docs/specs/`.

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
