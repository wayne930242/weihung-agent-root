# claude-drive-codex

Use Opus xhigh for main coordination and the [codex-first execution policy](codex-first.md) for delegated work.

Created: 2026-09-07.
Updated: 2026-09-12.
Rationale: The user requested the same cost-conscious execution policy as codex-first: Luna high for documentation, Sol high for investigation, Astra low for simple implementation, and Astra high for complex work.

## Selection and application

1. Apply the user's explicit model and effort override first; fill unspecified fields from the matching role or work category.
2. Main coordination covers requirements, routing, dispatch, tracking, and result integration. Use `--agent-kind claude --agent-model opus --agent-effort xhigh`.
3. For execution, read and apply the model table, selection order, escalation criteria, and parameter mapping in [codex-first](codex-first.md). This shared policy also covers small edits, lookup, documentation, routine review, and zero-defect requirements.
4. If the selected combination is unavailable, report the specific limitation and ask the user to choose an alternative.

Launch a main coordination session with `claude --model opus --effort xhigh`; use `--model 'opus[1m]'` when retaining the existing 1M context setting. The existing Claude launch mapping is retained. The profile defines selection preferences; session launch arguments determine the main session's actual model and effort. Authority handoff follows `handoff-orchestrator`.

## Usage and coordination

Measure total consumption across coordination, execution, handoffs, verification, and rework, including tokens, actual cost, and subscription quota.

Handle directly requested simple work in the current session. Delegate independently completable work with its objective, necessary context, evidence locations, and reality anchor. Add workers when independent work provides a clear parallel benefit.

The main agent retains requirements, decisions, dependencies, and result summaries. Workers own investigation, implementation, and verification within their scope and return outcomes, evidence locations, and unresolved questions. Coordinate through events and examine evidence when a contradiction or gap needs resolution. Lifecycle and authority follow Straw Boss `docs/roles.md`.

Native subagents and consultation tools use the same model and effort mapping. New dispatches use the active strategy; existing dispatch instructions retain their settings.
