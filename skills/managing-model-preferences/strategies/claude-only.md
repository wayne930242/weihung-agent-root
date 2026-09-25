# claude-only

The primary preference is to keep routine dispatch on Claude. Opus 5.5 high coordinates, low handles bounded edits and lookup, medium handles ordinary implementation and documents, and xhigh handles ambiguous complex work. The pinned Pi bridge advertises Opus 5.5 with a 1M context window for tiers that previously required 1M.

Created: 2026-09-07.
Updated: 2026-09-25.
Rationale: The user initially chose this profile when Codex quota was nearly exhausted. Later revisions separated complex work by environmental uncertainty, moved Fable's ambiguous tier to Opus 5.5 xhigh, raised main coordination to high, and retired Sonnet. During Pi migration, the user selected the upstream bridge commit that measures Opus 5.5 at 1M on Max and exposes that window in Pi.

## Pi tier rationale

Opus remains the preferred model for every tier. Pi keeps a Codex fallback for bridge outages, as required by the migration contract. Thinking ranges from low for bounded work to xhigh for ambiguous complex work.

The executable model, thinking, and fallback choices are in [Pi model profiles](../../../pi/model-profiles.json). Select the tier by the main deliverable and the task's uncertainty; an explicit user choice takes precedence. Pass the selected model and thinking level to each Pi dispatch.
