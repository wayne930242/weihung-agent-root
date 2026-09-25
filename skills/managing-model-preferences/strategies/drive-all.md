# drive-all

Multi-harness dispatch across Antigravity, Claude, and Codex: agy-medium for documentation, investigation, and source data cleaning and processing, Claude Opus 5.5 for implementation (low for simple, medium for standard and large code work), Codex sol-medium for UI/UX, Codex sol-low for routine review, Codex sol-high for complex work with clear instructions, Codex astra-low for complex work with unclear instructions, and Codex astra-high for academic research and forward-looking hard problems.

Created: 2026-09-14.
Updated: 2026-09-24.
Rationale: The user configured a multi-harness profile (drive-all): documentation, investigation, and source data cleaning and processing use agy-medium, simple implementation uses Claude sonnet low, standard implementation uses Claude sonnet high, UI/UX and routine review use Codex sol-low. The user then defined complexity as environmental unpredictability rather than code volume: large code work stays on Claude sonnet high, complex work uses Codex astra-low, and only complex work whose instructions are unclear and situation ambiguous uses Codex astra-high. On 2026-09-24 the user retired Sonnet and moved implementation to Opus 5.5: low for simple work, medium for standard work. The user also aligned the Codex tiers with claude-drive-codex: UI/UX on Sol medium, routine review on Sol low, complex work with clear instructions on Sol high, complex work with unclear instructions on Astra low, and Astra high reserved for academic research and forward-looking hard problems.

## Models and effort

| Work | agent-kind | agent-model | agent-effort |
|---|---|---|---|
| Documentation, writing, formatting, document conversion, investigation, research, lookup, information organization, and source data cleaning and processing | agy | gemini-3.8-flash | medium |
| UI/UX design review and visual audit | codex | gpt-6-sol | medium |
| Routine inspection | codex | gpt-6-sol | low |
| Simple localized implementation, small edits, mechanical tasks, and quick fixes | claude | claude-opus-5-5 | low |
| Standard feature implementation, refactoring, multi-file changes, and large code work in a predictable environment | claude | claude-opus-5-5 | medium |
| Complex work with clear instructions: the environment is unpredictable | codex | gpt-6-sol | high |
| Complex work with unclear instructions: the environment is unpredictable and the instructions or situation are ambiguous | codex | gpt-6-astra | low |
| Academic research and forward-looking hard problems | codex | gpt-6-astra | high |

## Selection order

1. Apply the user's explicit model and effort override first; fill unspecified fields from the matching work category.
2. Treat work as complex when its environment is unpredictable: external systems, runtime state, or data behave in ways the task cannot foresee, so the work must probe and adapt as it proceeds. Code volume, file count, cross-component edits, and verification strictness alone do not establish complexity.
3. Academic research and forward-looking hard problems use Astra high. For other complex work, choose Astra low when the instructions are unclear and the situation is ambiguous; otherwise choose Sol high. Verify the choice against the task's reality anchor.
4. Otherwise:
   - Use `agy` (Gemini 3.8 Flash, medium effort) for documentation, technical writing, formatting, investigation, codebase research, information organization, and source data cleaning or processing.
   - Use `codex` (Sol, medium effort) for UI/UX design reviews and visual inspections.
   - Use `codex` (Sol, low effort) for routine checks.
   - Use `claude` (Opus 5.5, low effort) for simple, localized, or mechanical code modifications.
   - Use `claude` (Opus 5.5, medium effort) for standard feature implementation, refactoring, and large code work in a predictable environment.
5. For a mixed task, choose the category that owns its main deliverable. Pass evidence and unresolved questions forward when findings establish environmental unpredictability or ambiguity.
6. If the selected combination is unavailable, report the specific limitation and ask the user to choose an alternative.

## Application

Pass the selected row explicitly as `--agent-kind`, `--agent-model`, and `--agent-effort` in the dispatch instruction:
- `agy`: uses `--model gemini-3.8-flash --effort medium`.
- `claude`: uses `--model claude-opus-5-5` with `--effort low` or `medium` for implementation.
- `codex`: uses `--model gpt-6-sol` with `-c model_reasoning_effort=high`, `medium`, or `low`, or `--model gpt-6-astra` with `-c model_reasoning_effort=low` or `high`.

Main coordination covers requirements, routing, dispatch, tracking, and result integration, and is determined by the active session's launch settings (defaulting to Claude Opus 5.5 1M high when launched from Claude Code, or Antigravity / Codex defaults respectively). Directly handled simple work continues in the current session. Execution and authority handoff follow Straw Boss skills and `i-am-orchestrator`.

For native subagents or consultation tools, map the same model and effort to their corresponding fields. New dispatches use the active strategy. Existing dispatch instructions retain their settings.

## Pi tier rationale

The former Gemini and agy document and investigation tier maps to Codex Luna medium, following the confirmed Pi migration choice. Opus remains the implementation tier; Sol and Astra retain their UI, review, and complex-work roles.

The executable model, thinking, and fallback choices are in [Pi model profiles](../../../pi/model-profiles.json). Select the tier by the main deliverable and the task's uncertainty; an explicit user choice takes precedence. Pass the selected model and thinking level to each Pi dispatch.
