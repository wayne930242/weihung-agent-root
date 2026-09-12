# Model Preference Profile

Active strategy: [codex-first](strategies/codex-first.md).
Activated: 2026-09-12.
Rationale: The user requested Codex first with lower Astra spending: documentation uses Luna high, investigation uses Sol high, simple implementation uses Astra low, and complex work uses Astra high. The same execution policy applies to claude-drive-codex.

Before running `boss-say` or selecting a delegated model, read this entrypoint and the complete active strategy. Follow its model and effort selection rules. The user's explicit choice for the current task takes priority. New dispatches use the current strategy; existing dispatch instructions retain their settings.

## Strategies

| Strategy | Purpose |
|---|---|
| [claude-only](strategies/claude-only.md) | Claude execution: Opus xhigh coordination, Sonnet low small tasks, Sonnet high standard implementation, Fable 5.1 medium complex work |
| [claude-drive-codex](strategies/claude-drive-codex.md) | Opus xhigh coordination with the shared codex-first execution policy |
| [codex-drive-claude](strategies/codex-drive-claude.md) | Codex coordination, Sonnet small and standard tasks, Opus complex tasks, Codex low documentation |
| [codex-first](strategies/codex-first.md) | Luna high documentation, Sol high investigation, Astra low implementation, Astra high complex work |
| [claude-coding-codex-doc](strategies/claude-coding-codex-doc.md) | Claude coding, investigation, and lookup; Codex documentation |

## Version control

Store each strategy in `strategies/<name>.md` and track revisions in Git. Switching strategies updates this entrypoint's active link, date, and rationale. Register new strategies in the table. Manage changes through the `managing-model-preferences` skill.
