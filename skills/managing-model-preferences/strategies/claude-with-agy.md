# claude-with-agy

Two-harness dispatch across Antigravity and Claude with no Codex usage: agy-medium for documentation, investigation, source data cleaning and processing, UI/UX and routine review, Claude Opus 5.5 for implementation (low for simple, medium for standard and large code work), Claude Opus 5.5 1M low for complex work, and Claude Opus 5.5 1M xhigh for complex work with unclear instructions.

Created: 2026-09-15.
Updated: 2026-09-24.
Rationale: The user requested a drive-all variant that consumes no Codex tokens: Astra low becomes Claude opus[1m] and Astra high becomes Claude Fable 5.1, each keeping its effort level, and the user chose agy-medium to replace Codex sol-low for UI/UX and routine review, keeping a non-Claude review perspective. On 2026-09-23 the user replaced Fable 5.1 high with Opus 5.5 1M xhigh and pinned Opus to 5.5. On 2026-09-24 the user retired Sonnet and moved implementation to Opus 5.5: low for simple work, medium for standard work.

## Models and effort

| Work | agent-kind | agent-model | agent-effort |
|---|---|---|---|
| Documentation, writing, formatting, document conversion, investigation, research, lookup, information organization, and source data cleaning and processing | agy | gemini-3.8-flash | medium |
| UI/UX design review, visual audit, and routine inspection | agy | gemini-3.8-flash | medium |
| Simple localized implementation, small edits, mechanical tasks, and quick fixes | claude | claude-opus-5-5 | low |
| Standard feature implementation, refactoring, multi-file changes, and large code work in a predictable environment | claude | claude-opus-5-5 | medium |
| Complex work with clear instructions: the environment is unpredictable | claude | claude-opus-5-5[1m] | low |
| Complex work with unclear instructions: the environment is unpredictable and the instructions or situation are ambiguous | claude | claude-opus-5-5[1m] | xhigh |

## Selection order

1. Apply the user's explicit model and effort override first; fill unspecified fields from the matching work category.
2. Treat work as complex when its environment is unpredictable: external systems, runtime state, or data behave in ways the task cannot foresee, so the work must probe and adapt as it proceeds. Code volume, file count, cross-component edits, and verification strictness alone do not establish complexity.
3. For complex work, choose Opus 5.5 1M xhigh when the instructions are unclear and the situation is ambiguous; otherwise choose Opus 5.5 1M low. Verify the choice against the task's reality anchor.
4. Otherwise:
   - Use `agy` (Gemini 3.8 Flash, medium effort) for documentation, technical writing, formatting, investigation, codebase research, information organization, source data cleaning or processing, UI/UX design reviews, visual inspections, and routine checks.
   - Use `claude` (Opus 5.5, low effort) for simple, localized, or mechanical code modifications.
   - Use `claude` (Opus 5.5, medium effort) for standard feature implementation, refactoring, and large code work in a predictable environment.
5. For a mixed task, choose the category that owns its main deliverable. Pass evidence and unresolved questions forward when findings establish environmental unpredictability or ambiguity.
6. Route every case that CLAUDE.md assigns to Codex (the UI/UX design refinement pass and direct cross-model consultation) to `agy` (Gemini 3.8 Flash, medium effort) through the same transport that rule requires. This strategy dispatches no work to Codex.
7. If the selected combination is unavailable, report the specific limitation and ask the user to choose an alternative.

## Application

Pass the selected row explicitly as `--agent-kind`, `--agent-model`, and `--agent-effort` in the dispatch instruction:
- `agy`: uses `--model gemini-3.8-flash --effort medium`.
- `claude`: uses `--model claude-opus-5-5` with `--effort low` or `medium`, `--model 'claude-opus-5-5[1m]' --effort low`, or `--model 'claude-opus-5-5[1m]' --effort xhigh`.

Main coordination covers requirements, routing, dispatch, tracking, and result integration, and is determined by the active session's launch settings (defaulting to Claude Opus 5.5 1M high when launched from Claude Code, or Antigravity defaults respectively). Directly handled simple work continues in the current session. Execution and authority handoff follow Straw Boss skills and `i-am-orchestrator`.

For native subagents or consultation tools, map the same model and effort to their corresponding fields. New dispatches use the active strategy. Existing dispatch instructions retain their settings.
