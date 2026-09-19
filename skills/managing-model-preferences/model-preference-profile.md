# Model Preference Profile

Active strategy: [claude-drive-codex](strategies/claude-drive-codex.md).
Activated: 2026-09-19.
Rationale: The user directed a switch to claude-drive-codex, so dispatch returns to Codex tiers while agy stays unused:
- Opus xhigh coordinates.
- Codex Luna medium handles documentation, investigation and data processing.
- Sonnet low and high handle simple and standard implementation.
- Codex Sol low handles UI/UX and routine review.
- Codex Astra low and high handle complex work with clear and with unclear instructions.

Before running `boss-say` or selecting a delegated model, read this entrypoint and the complete active strategy. Follow its model and effort selection rules. The user's explicit choice for the current task takes priority. New dispatches use the current strategy; existing dispatch instructions retain their settings.

## Strategies

| Strategy | Purpose |
|---|---|
| [claude-with-agy](strategies/claude-with-agy.md) | No-Codex drive-all variant: agy-medium docs, investigation, data processing, UI/UX and routine review, Sonnet simple (low) and standard (high) implementation, Opus 1M low complex work, Fable 5.1 high complex work with unclear instructions |
| [drive-all](strategies/drive-all.md) | Multi-harness dispatch: agy-medium docs, investigation, and source data cleaning/processing, Sonnet simple (low) and standard (high) implementation, Sol low UI/UX and routine review, Astra low complex work, Astra high complex work with unclear instructions |
| [claude-only](strategies/claude-only.md) | Claude-only execution: Opus xhigh coordination, Sonnet low small tasks, Sonnet high standard implementation and routine review, Opus 1M low UI/UX and complex work, Fable 5.1 high complex work with unclear instructions |
| [claude-drive-codex](strategies/claude-drive-codex.md) | No-agy drive-all variant: Opus xhigh coordination, Codex luna-medium docs, investigation, and source data cleaning/processing, Sonnet simple (low) and standard (high) implementation, Sol low UI/UX and routine review, Astra low complex work, Astra high complex work with unclear instructions |
| [codex-drive-claude](strategies/codex-drive-claude.md) | Codex coordination, Sonnet small and standard tasks, Opus complex tasks, Codex low documentation |
| [codex-first](strategies/codex-first.md) | Luna high documentation, Sol high investigation, Astra low implementation, Astra high complex work |
| [claude-coding-codex-doc](strategies/claude-coding-codex-doc.md) | Claude coding, investigation, and lookup; Codex documentation |

## Version control

Store each strategy in `strategies/<name>.md` and track revisions in Git. Switching strategies updates this entrypoint's active link, date, and rationale. Register new strategies in the table. Manage changes through the `managing-model-preferences` skill.
