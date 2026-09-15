# drive-all

Multi-harness dispatch across Antigravity, Claude, and Codex: agy-medium for documentation, investigation, and source data cleaning and processing, Claude sonnet for implementation (low for simple, high for standard and large code work), Codex sol-low for UI/UX and routine review, Codex astra-low for complex work, and Codex astra-high for complex work with unclear instructions.

Created: 2026-09-14.
Updated: 2026-09-15.
Rationale: The user configured a multi-harness profile (drive-all): documentation, investigation, and source data cleaning and processing use agy-medium, simple implementation uses Claude sonnet low, standard implementation uses Claude sonnet high, UI/UX and routine review use Codex sol-low. The user then defined complexity as environmental unpredictability rather than code volume: large code work stays on Claude sonnet high, complex work uses Codex astra-low, and only complex work whose instructions are unclear and situation ambiguous uses Codex astra-high.

## Models and effort

| Work | agent-kind | agent-model | agent-effort |
|---|---|---|---|
| Documentation, writing, formatting, document conversion, investigation, research, lookup, information organization, and source data cleaning and processing | agy | gemini-3.8-flash | medium |
| UI/UX design review, visual audit, and routine inspection | codex | gpt-5.6-sol | low |
| Simple localized implementation, small edits, mechanical tasks, and quick fixes | claude | sonnet | low |
| Standard feature implementation, refactoring, multi-file changes, and large code work in a predictable environment | claude | sonnet | high |
| Complex work with clear instructions: the environment is unpredictable | codex | gpt-6-astra | low |
| Complex work with unclear instructions: the environment is unpredictable and the instructions or situation are ambiguous | codex | gpt-6-astra | high |

## Selection order

1. Apply the user's explicit model and effort override first; fill unspecified fields from the matching work category.
2. Treat work as complex when its environment is unpredictable: external systems, runtime state, or data behave in ways the task cannot foresee, so the work must probe and adapt as it proceeds. Code volume, file count, cross-component edits, and verification strictness alone do not establish complexity.
3. For complex work, choose Astra high when the instructions are unclear and the situation is ambiguous; otherwise choose Astra low. Verify the choice against the task's reality anchor.
4. Otherwise:
   - Use `agy` (Gemini 3.8 Flash, medium effort) for documentation, technical writing, formatting, investigation, codebase research, information organization, and source data cleaning or processing.
   - Use `codex` (Sol, low effort) for UI/UX design reviews, visual inspections, and routine checks.
   - Use `claude` (Sonnet, low effort) for simple, localized, or mechanical code modifications.
   - Use `claude` (Sonnet, high effort) for standard feature implementation, refactoring, and large code work in a predictable environment.
5. For a mixed task, choose the category that owns its main deliverable. Pass evidence and unresolved questions forward when findings establish environmental unpredictability or ambiguity.
6. If the selected combination is unavailable, report the specific limitation and ask the user to choose an alternative.

## Application

Pass the selected row explicitly as `--agent-kind`, `--agent-model`, and `--agent-effort` in the dispatch instruction:
- `agy`: uses `--model gemini-3.8-flash --effort medium`.
- `claude`: uses `--model sonnet` with `--effort low` or `high`.
- `codex`: uses `--model gpt-5.6-sol` with `-c model_reasoning_effort=low`, or `--model gpt-6-astra` with `-c model_reasoning_effort=low` or `high`.

Main coordination covers requirements, routing, dispatch, tracking, and result integration, and is determined by the active session's launch settings (defaulting to Claude Opus xhigh when launched from Claude Code, or Antigravity / Codex defaults respectively). Directly handled simple work continues in the current session. Execution and authority handoff follow Straw Boss skills and `docs/roles.md`.

For native subagents or consultation tools, map the same model and effort to their corresponding fields. New dispatches use the active strategy. Existing dispatch instructions retain their settings.
