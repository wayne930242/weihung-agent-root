# claude-drive-codex

Claude-coordinated dispatch across Claude and Codex with no Antigravity usage: Opus 5.5 high for main coordination, Codex luna-high for documentation, Codex luna-medium for investigation and source data cleaning and processing, Claude sonnet for implementation (low for simple, high for standard and large code work), Codex sol-medium for UI/UX, Codex sol-low for routine review, Codex astra-low for complex work, and Codex astra-high for complex work with unclear instructions.

Created: 2026-09-07.
Updated: 2026-09-23.
Rationale: The user asked to align this strategy with drive-all and replace the agy tier with Codex's low-tier model. OpenAI's Codex model guide positions GPT-6 Luna as the lowest-cost GPT-6 model for clear, repeatable work such as extraction, transformation, and structured summaries. This strategy keeps drive-all's medium effort for that tier. On 2026-09-23 the user raised documentation to Luna high and UI/UX work to Sol medium; investigation and data processing stay on Luna medium, and routine inspection stays on Sol low.

## Models and effort

| Role or work | agent-kind | agent-model | agent-effort |
|---|---|---|---|
| Main coordination: requirements, routing, dispatch, tracking, and result integration | claude | claude-opus-5-5 | high |
| Documentation, writing, formatting, and document conversion | codex | gpt-6-luna | high |
| Investigation, research, lookup, information organization, and source data cleaning and processing | codex | gpt-6-luna | medium |
| UI/UX design review and visual audit | codex | gpt-6-sol | medium |
| Routine inspection | codex | gpt-6-sol | low |
| Simple localized implementation, small edits, mechanical tasks, and quick fixes | claude | sonnet | low |
| Standard feature implementation, refactoring, multi-file changes, and large code work in a predictable environment | claude | sonnet | high |
| Complex work with clear instructions: the environment is unpredictable | codex | gpt-6-astra | low |
| Complex work with unclear instructions: the environment is unpredictable and the instructions or situation are ambiguous | codex | gpt-6-astra | high |

## Selection order

1. Apply the user's explicit model and effort override first; fill unspecified fields from the matching role or work category.
2. Main coordination uses Opus 5.5 high.
3. Treat work as complex when its environment is unpredictable: external systems, runtime state, or data behave in ways the task cannot foresee, so the work must probe and adapt as it proceeds. Code volume, file count, cross-component edits, and verification strictness alone do not establish complexity.
4. For complex work, choose Astra high when the instructions are unclear and the situation is ambiguous; otherwise choose Astra low. Verify the choice against the task's reality anchor.
5. Otherwise:
   - Use `codex` (Luna, high effort) for documentation, technical writing, formatting, and document conversion.
   - Use `codex` (Luna, medium effort) for investigation, codebase research, information organization, and source data cleaning or processing.
   - Use `codex` (Sol, medium effort) for UI/UX design reviews and visual inspections.
   - Use `codex` (Sol, low effort) for routine checks.
   - Use `claude` (Sonnet, low effort) for simple, localized, or mechanical code modifications.
   - Use `claude` (Sonnet, high effort) for standard feature implementation, refactoring, and large code work in a predictable environment.
6. For a mixed task, choose the category that owns its main deliverable. Pass evidence and unresolved questions forward when findings establish environmental unpredictability or ambiguity.
7. If the selected combination is unavailable, report the specific limitation and ask the user to choose an alternative.

## Application

Pass the selected row explicitly as `--agent-kind`, `--agent-model`, and `--agent-effort` in the dispatch instruction:
- `claude`: uses `--model sonnet` with `--effort low` or `high`.
- `codex`: uses `--model gpt-6-luna` with `-c model_reasoning_effort=high` or `medium`, `--model gpt-6-sol` with `-c model_reasoning_effort=medium` or `low`, or `--model gpt-6-astra` with `-c model_reasoning_effort=low` or `high`.

Launch a main coordination session with `claude --model claude-opus-5-5 --effort high`; use `--model 'claude-opus-5-5[1m]'` when retaining the existing 1M context setting. The profile defines selection preferences; session launch arguments determine the main session's actual model and effort. Directly handled simple work continues in the current session. Execution and authority handoff follow Straw Boss skills, `handoff-orchestrator`, and `i-am-orchestrator`.

For native subagents or consultation tools, map the same model and effort to their corresponding fields. New dispatches use the active strategy. Existing dispatch instructions retain their settings.
