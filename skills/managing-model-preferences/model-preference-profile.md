# Model Preference Profile

Active strategy: [claude-drive-codex](strategies/claude-drive-codex.md).
Activated: 2026-09-23.
Updated: 2026-09-24.
Rationale: Codex quota has been reset, so Codex returns to its tiers while agy stays off; Sonnet is retired and Opus 5.5 takes implementation:
- Opus 5.5 high handles main coordination.
- Codex Luna (gpt-6-luna) high handles documentation; Luna medium handles investigation and source data processing.
- Opus 5.5 low and medium handle simple and standard implementation.
- Codex Sol (gpt-6-sol) medium handles UI/UX; Sol low handles routine review.
- Codex Sol high handles complex work with clear instructions; Astra low handles complex work with unclear instructions.
- Codex Astra high is reserved for academic research and forward-looking hard problems.

Before running `boss-say` or selecting a delegated model, read this entrypoint and the complete active strategy. Follow its model and effort selection rules. The user's explicit choice for the current task takes priority. New dispatches use the current strategy; existing dispatch instructions retain their settings.

## Strategies

| Strategy | Purpose |
|---|---|
| [claude-with-agy](strategies/claude-with-agy.md) | No-Codex drive-all variant: agy-medium docs, investigation, data processing, UI/UX and routine review, Opus 5.5 simple (low) and standard (medium) implementation, Opus 5.5 1M low complex work, Opus 5.5 1M xhigh complex work with unclear instructions |
| [drive-all](strategies/drive-all.md) | Multi-harness dispatch: agy-medium docs, investigation, and source data cleaning/processing, Opus 5.5 simple (low) and standard (medium) implementation, Sol medium UI/UX, Sol low routine review, Sol high complex work, Astra low complex work with unclear instructions, Astra high academic research and forward-looking hard problems |
| [claude-only](strategies/claude-only.md) | Claude-only execution: Opus 5.5 high coordination, Opus 5.5 low small tasks, Opus 5.5 medium standard implementation and routine review, Opus 5.5 1M low UI/UX and complex work, Opus 5.5 1M xhigh complex work with unclear instructions |
| [claude-drive-codex](strategies/claude-drive-codex.md) | No-agy drive-all variant: Opus 5.5 high coordination, Codex luna-high docs, luna-medium investigation and source data cleaning/processing, Opus 5.5 simple (low) and standard (medium) implementation, Sol medium UI/UX, Sol low routine review, Sol high complex work, Astra low complex work with unclear instructions, Astra high academic research and forward-looking hard problems |
| [codex-drive-claude](strategies/codex-drive-claude.md) | claude-drive-codex tiers under a Codex main session |
| [codex-first](strategies/codex-first.md) | claude-drive-codex tiers without a fixed coordination model: main session follows its launch settings |
| [claude-coding-codex-doc](strategies/claude-coding-codex-doc.md) | Claude Opus 5.5 medium coding, investigation, and lookup; Codex documentation |

## Version control

Store each strategy in `strategies/<name>.md` and track revisions in Git. Switching strategies updates this entrypoint's active link, date, and rationale. Register new strategies in the table. Manage changes through the `managing-model-preferences` skill.
