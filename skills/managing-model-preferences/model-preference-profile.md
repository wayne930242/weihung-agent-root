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

Before selecting a delegated model, read this entrypoint and the active strategy's Pi tiers. The user's explicit choice for the current task takes priority. New dispatches use the current strategy; existing dispatches retain their settings.

[pi/model-profiles.json](../../pi/model-profiles.json) holds each strategy's exact `provider/model-id` and thinking level per tier. After switching the active strategy, run `python3 scripts/pi-target.py apply-profile --home "$HOME"` from the repository and reload pi; it regenerates `~/.pi/agent/AGENTS.md` and updates the pi default model and `pi-herdr-agents` task candidates.

## Tier guide

1. Apply the user's explicit model and thinking override first; fill unspecified fields from the matching tier.
2. `main` is the coordinating session: requirements, routing, dispatch, tracking, and result integration.
3. Treat work as complex when its environment is unpredictable: external systems, runtime state, or data behave in ways the task cannot foresee, so the work must probe and adapt as it proceeds. Code volume, file count, cross-component edits, and verification strictness alone do not establish complexity.
4. Academic research and forward-looking hard problems use `academic`. Other complex work uses `complex_unclear` when the instructions are unclear and the situation is ambiguous, otherwise `complex_clear`. Verify the choice against the task's reality anchor.
5. Otherwise:
   - `docs`: documentation, technical writing, formatting, and document conversion.
   - `recon`: investigation, codebase research, information organization, and source data cleaning or processing.
   - `ui`: UI/UX design review and visual inspection.
   - `review`: routine checks and code review.
   - `simple`: simple, localized, or mechanical code changes.
   - `coding`: standard feature implementation, refactoring, and large code work in a predictable environment.
6. For a mixed task, choose the tier that owns its main deliverable. Pass evidence and unresolved questions forward when findings establish environmental unpredictability or ambiguity.
7. If the selected model is unavailable, use the next candidate in the tier's list from `~/.pi/agent/AGENTS.md` and report the substitution.

## Strategies

| Strategy | Purpose |
|---|---|
| [claude-with-agy](strategies/claude-with-agy.md) | Codex-light: Luna medium for documents, investigation, UI, and review; Opus 5.5 for implementation and all complex work |
| [drive-all](strategies/drive-all.md) | claude-drive-codex tiers with Luna medium documents |
| [claude-only](strategies/claude-only.md) | Opus 5.5 for every tier, thinking low to xhigh |
| [claude-drive-codex](strategies/claude-drive-codex.md) | Opus 5.5 high coordination and implementation (low/medium); Luna high docs and medium investigation; Sol medium UI, low review, high clear complex work; Astra low ambiguous complex work, high academic research |
| [codex-drive-claude](strategies/codex-drive-claude.md) | claude-drive-codex tiers under a Sol high main session |
| [codex-first](strategies/codex-first.md) | Same pi tiers as codex-drive-claude |
| [claude-coding-codex-doc](strategies/claude-coding-codex-doc.md) | Opus 5.5 coding, investigation, and review; Luna documents; Sol UI |

## Version control

Store each strategy's rationale and tier table in `strategies/<name>.md` and its executable tiers in `pi/model-profiles.json`; track revisions in Git. Switching strategies updates this entrypoint's active link, date, and rationale. Register new strategies in the table. Manage changes through the `managing-model-preferences` skill.
