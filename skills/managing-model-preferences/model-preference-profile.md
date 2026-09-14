# Model Preference Profile

Active strategy: [drive-all](strategies/drive-all.md).
Activated: 2026-09-14.
Rationale: The user requested a drive-all profile spanning all harnesses: documentation, investigation, and source data cleaning/processing use agy-medium, simple implementation uses Claude sonnet low, standard implementation uses Claude sonnet high, UI/UX and general review use Codex sol-low, and complex implementation uses Codex astra-high.

Before running `boss-say` or selecting a delegated model, read this entrypoint and the complete active strategy. Follow its model and effort selection rules. The user's explicit choice for the current task takes priority. New dispatches use the current strategy; existing dispatch instructions retain their settings.

## Strategies

| Strategy | Purpose |
|---|---|
| [drive-all](strategies/drive-all.md) | Multi-harness dispatch: agy-medium docs, investigation, and source data cleaning/processing, Sonnet simple (low) and standard (high) implementation, Sol low UI/UX and routine review, Astra high complex work |
| [claude-only](strategies/claude-only.md) | Claude execution: Opus xhigh coordination, Sonnet low small tasks, Sonnet high standard implementation, Fable 5.1 medium complex work |
| [claude-drive-codex](strategies/claude-drive-codex.md) | Opus xhigh coordination with the shared codex-first execution policy |
| [codex-drive-claude](strategies/codex-drive-claude.md) | Codex coordination, Sonnet small and standard tasks, Opus complex tasks, Codex low documentation |
| [codex-first](strategies/codex-first.md) | Luna high documentation, Sol high investigation, Astra low implementation, Astra high complex work |
| [claude-coding-codex-doc](strategies/claude-coding-codex-doc.md) | Claude coding, investigation, and lookup; Codex documentation |

## Version control

Store each strategy in `strategies/<name>.md` and track revisions in Git. Switching strategies updates this entrypoint's active link, date, and rationale. Register new strategies in the table. Manage changes through the `managing-model-preferences` skill.
