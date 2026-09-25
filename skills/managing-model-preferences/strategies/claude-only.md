# claude-only

The primary preference is to keep routine dispatch on Claude. Opus 5.5 high coordinates, low handles bounded edits and lookup, medium handles ordinary implementation and documents, and xhigh handles ambiguous complex work. The pinned Pi bridge advertises Opus 5.5 with a 1M context window for tiers that previously required 1M.

Created: 2026-09-07.
Updated: 2026-09-25.
Rationale: The user initially chose this profile when Codex quota was nearly exhausted. Later revisions separated complex work by environmental uncertainty, moved Fable's ambiguous tier to Opus 5.5 xhigh, raised main coordination to high, and retired Sonnet. During Pi migration, the user selected the upstream bridge commit that measures Opus 5.5 at 1M on Max and exposes that window in Pi.

## Models and effort

| Role or work | agent-kind | agent-model | agent-effort |
|---|---|---|---|
| Main coordination: requirements, routing, dispatch, tracking, and result integration | claude | claude-opus-5-5 | high |
| Small, local, verifiable changes and mechanical work | claude | claude-opus-5-5 | low |
| Directed lookup, information organization, and status checks | claude | claude-opus-5-5 | low |
| Standard implementation, refactoring, multi-file changes, writing, routine analysis and review, and large code work in a predictable environment | claude | claude-opus-5-5 | medium |
| UI/UX design review, visual audit, and routine inspection | claude | claude-opus-5-5[1m] | low |
| Complex work with clear instructions: the environment is unpredictable | claude | claude-opus-5-5[1m] | low |
| Complex work with unclear instructions: the environment is unpredictable and the instructions or situation are ambiguous | claude | claude-opus-5-5[1m] | xhigh |

## Selection order

1. Apply the user's explicit model and effort override first; fill unspecified fields from the matching row.
2. Main coordination uses Opus 5.5 high.
3. Treat work as complex when its environment is unpredictable: external systems, runtime state, or data require probing and adaptation. Code volume, file count, cross-component edits, and verification strictness alone do not establish complexity.
4. For complex work, choose Opus 5.5 1M xhigh when instructions and context are ambiguous; otherwise choose Opus 5.5 1M low. Check the choice against the task's reality anchor.
5. For other work, use Opus 5.5 low for bounded changes, mechanical work, lookup, formatting, conversion, and extraction; Opus 5.5 medium for ordinary implementation, substantial writing, analysis, and review; and Opus 5.5 1M low for visual work.
6. For mixed work, follow the main deliverable. Escalate from low to medium when reasoning or implementation expands, and to 1M tiers when evidence establishes environmental unpredictability.
7. Route cases that CLAUDE.md assigns to Codex through the matching Claude row and required transport. State when a cross-model perspective was unavailable.
8. If a selected combination is unavailable, report the limitation and ask the user to choose an alternative.

## Application

Pass the selected row as `--agent-kind`, `--agent-model`, and `--agent-effort` in each dispatch instruction. Use `claude --model claude-opus-5-5 --effort high` for a new main coordination session. Use `--model 'claude-opus-5-5[1m]'` for a 1M tier and pass `low` or `xhigh` as selected. Session launch arguments determine the active main model and effort; the profile defines selection preferences. Native subagents and consultation tools use the corresponding model and effort fields. New dispatches use the active strategy; existing dispatch instructions retain their settings.

## Pi tier rationale

Opus remains the preferred model for every tier. Pi keeps a Codex fallback for bridge outages, as required by the migration contract. Thinking ranges from low for bounded work to xhigh for ambiguous complex work.

The executable model, thinking, and fallback choices are in [Pi model profiles](../../../pi/model-profiles.json). Select the tier by the main deliverable and the task's uncertainty; an explicit user choice takes precedence. Pass the selected model and thinking level to each Pi dispatch.
