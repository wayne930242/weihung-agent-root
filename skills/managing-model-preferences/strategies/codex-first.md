# codex-first

Prefer Codex for delegated execution, choosing the model by work type and using Astra high for complex work.

Created: 2026-09-07.
Updated: 2026-09-12.
Rationale: The user requested lower Astra spending, Luna high for documentation, Sol high for investigation, Astra low for simple implementation, and Astra high for complex work.

## Models and effort

| Work | agent-kind | agent-model | agent-effort |
|---|---|---|---|
| Documentation, writing, formatting, and document conversion | codex | gpt-5.6-luna | high |
| Investigation, research, lookup, information organization, status checks, routine analysis, and review | codex | gpt-5.6-sol | high |
| Simple and standard implementation with clear requirements and a verifiable result | codex | gpt-6-astra | low |
| Complex work: cross-component reasoning, difficult diagnosis, major design decisions, or an explicit zero-defect requirement | codex | gpt-6-astra | high |

## Selection order

1. Apply the user's explicit model and effort override first; fill unspecified fields from the matching work category.
2. Choose Astra high when the work requires complex reasoning, major design judgment, or an explicit zero-defect requirement. Apply this criterion across all work types and verify against the task's reality anchor.
3. Otherwise, choose Luna high for documentation, Sol high for investigation and routine analysis or review, and Astra low for simple or standard implementation. Research depth or document length alone does not establish complexity; use the reasoning and uncertainty required by the task.
4. For a mixed task, choose the category that owns its main deliverable. Pass evidence and unresolved questions forward when findings establish a need for Astra high.
5. If the selected combination is unavailable, report the specific limitation and ask the user to choose an alternative.

## Application

Pass the selected row explicitly as `--agent-kind`, `--agent-model`, and `--agent-effort` in the dispatch instruction. The current harness model list verifies `gpt-5.6-luna` with `high`, `gpt-5.6-sol` with `high`, and `gpt-6-astra` with `low` or `high`. Names such as Astra high are preference labels; model and effort remain separate arguments.

For native subagents or consultation tools, map the same model and effort to their corresponding fields and choose a role that accepts the combination. This profile selects delegated execution models; the main session's model is determined by its launch settings. Directly handled simple work continues in the current session. Execution and authority handoff follow Straw Boss skills and `docs/roles.md`.

New dispatches use the active strategy. Existing dispatch instructions retain their settings.
