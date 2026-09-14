# drive-all

Multi-harness dispatch across Antigravity, Claude, and Codex: agy-medium for documentation, investigation, and source data cleaning and processing, Claude sonnet for implementation (low for simple, high for standard), Codex sol-low for UI/UX and routine review, and Codex astra-high for complex work.

Created: 2026-09-14.
Rationale: The user configured a multi-harness profile (drive-all): documentation, investigation, and source data cleaning and processing use agy-medium, simple implementation uses Claude sonnet low, standard implementation uses Claude sonnet high, UI/UX and routine review use Codex sol-low, and complex implementation uses Codex astra-high.

## Models and effort

| Work | agent-kind | agent-model | agent-effort |
|---|---|---|---|
| Documentation, writing, formatting, document conversion, investigation, research, lookup, information organization, and source data cleaning and processing | agy | gemini-3.8-flash | medium |
| UI/UX design review, visual audit, and routine inspection | codex | gpt-5.6-sol | low |
| Simple localized implementation, small edits, mechanical tasks, and quick fixes | claude | sonnet | low |
| Standard feature implementation, refactoring, and multi-file changes with clear specifications | claude | sonnet | high |
| Complex work: cross-component reasoning, difficult diagnosis, major design decisions, or zero-defect requirements | codex | gpt-6-astra | high |

## Selection order

1. Apply the user's explicit model and effort override first; fill unspecified fields from the matching work category.
2. Choose Astra high when the work requires complex reasoning, difficult diagnosis, major design judgment, or an explicit zero-defect requirement. Apply this criterion across all work types and verify against the task's reality anchor.
3. Otherwise:
   - Use `agy` (Gemini 3.8 Flash, medium effort) for documentation, technical writing, formatting, investigation, codebase research, information organization, and source data cleaning or processing.
   - Use `codex` (Sol, low effort) for UI/UX design reviews, visual inspections, and routine checks.
   - Use `claude` (Sonnet, low effort) for simple, localized, or mechanical code modifications.
   - Use `claude` (Sonnet, high effort) for standard feature implementation and broader code changes with clear specifications.
4. For a mixed task, choose the category that owns its main deliverable. Pass evidence and unresolved questions forward when findings establish a need for Astra high.
5. If the selected combination is unavailable, report the specific limitation and ask the user to choose an alternative.

## Application

Pass the selected row explicitly as `--agent-kind`, `--agent-model`, and `--agent-effort` in the dispatch instruction:
- `agy`: uses `--model gemini-3.8-flash --effort medium`.
- `claude`: uses `--model sonnet` with `--effort low` or `high`.
- `codex`: uses `--model gpt-5.6-sol` with `-c model_reasoning_effort=low` or `--model gpt-6-astra` with `-c model_reasoning_effort=high`.

Main coordination covers requirements, routing, dispatch, tracking, and result integration, and is determined by the active session's launch settings (defaulting to Claude Opus xhigh when launched from Claude Code, or Antigravity / Codex defaults respectively). Directly handled simple work continues in the current session. Execution and authority handoff follow Straw Boss skills and `docs/roles.md`.

For native subagents or consultation tools, map the same model and effort to their corresponding fields. New dispatches use the active strategy. Existing dispatch instructions retain their settings.
