# codex-first

Prefer Codex for delegated non-implementation work with the same tiers as claude-drive-codex: Codex luna-high for documentation, Codex luna-medium for investigation and source data cleaning and processing, Codex sol-medium for UI/UX, Codex sol-low for routine review, Claude Opus 5.5 for implementation (low for simple, medium for standard and large code work), Codex sol-high for complex work with clear instructions, Codex astra-low for complex work with unclear instructions, and Codex astra-high for academic research and forward-looking hard problems.

Created: 2026-09-07.
Updated: 2026-09-24.
Rationale: The user requested lower Astra spending, Luna high for documentation, Sol high for investigation, Astra low for simple implementation, and Astra high for complex work.
On 2026-09-24 the user aligned this strategy with claude-drive-codex: investigation moves to Luna medium, routine review to Sol low, UI/UX to Sol medium, implementation to Claude Opus 5.5 low and medium, complex work to Sol high or Astra low by instruction clarity, and Astra high is reserved for academic research and forward-looking hard problems.

## Models and effort

| Work | agent-kind | agent-model | agent-effort |
|---|---|---|---|
| Documentation, writing, formatting, and document conversion | codex | gpt-6-luna | high |
| Investigation, research, lookup, information organization, and source data cleaning and processing | codex | gpt-6-luna | medium |
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
   - Use `codex` (Luna, high effort) for documentation, technical writing, formatting, and document conversion.
   - Use `codex` (Luna, medium effort) for investigation, codebase research, information organization, and source data cleaning or processing.
   - Use `codex` (Sol, medium effort) for UI/UX design reviews and visual inspections.
   - Use `codex` (Sol, low effort) for routine checks.
   - Use `claude` (Opus 5.5, low effort) for simple, localized, or mechanical code modifications.
   - Use `claude` (Opus 5.5, medium effort) for standard feature implementation, refactoring, and large code work in a predictable environment.
5. For a mixed task, choose the category that owns its main deliverable. Pass evidence and unresolved questions forward when findings establish environmental unpredictability or ambiguity.
6. If the selected combination is unavailable, report the specific limitation and ask the user to choose an alternative.

## Application

Pass the selected row explicitly as `--agent-kind`, `--agent-model`, and `--agent-effort` in the dispatch instruction:
- `claude`: uses `--model claude-opus-5-5` with `--effort low` or `medium`.
- `codex`: uses `--model gpt-6-luna` with `-c model_reasoning_effort=high` or `medium`, `--model gpt-6-sol` with `-c model_reasoning_effort=high`, `medium`, or `low`, or `--model gpt-6-astra` with `-c model_reasoning_effort=low` or `high`.

For native subagents or consultation tools, map the same model and effort to their corresponding fields and choose a role that accepts the combination. This profile selects delegated execution models; the main session's model is determined by its launch settings. Directly handled simple work continues in the current session. Execution and authority handoff follow Straw Boss skills and `i-am-orchestrator`.

New dispatches use the active strategy. Existing dispatch instructions retain their settings.
