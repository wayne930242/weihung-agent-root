# claude-with-agy

Two-harness dispatch across Antigravity and Claude with no Codex usage: agy-medium for documentation, investigation, source data cleaning and processing, UI/UX and routine review, Claude Opus 5.5 for implementation (low for simple, medium for standard and large code work), Claude Opus 5.5 1M low for complex work, and Claude Opus 5.5 1M xhigh for complex work with unclear instructions.

Created: 2026-09-15.
Updated: 2026-09-24.
Rationale: The user requested a drive-all variant that consumes no Codex tokens: Astra low becomes Claude opus[1m] and Astra high becomes Claude Fable 5.1, each keeping its effort level, and the user chose agy-medium to replace Codex sol-low for UI/UX and routine review, keeping a non-Claude review perspective. On 2026-09-23 the user replaced Fable 5.1 high with Opus 5.5 1M xhigh and pinned Opus to 5.5. On 2026-09-24 the user retired Sonnet and moved implementation to Opus 5.5: low for simple work, medium for standard work.

## Pi tier rationale

The former Gemini and agy lightweight tiers map to Codex Luna medium, following the confirmed Pi migration choice. Opus handles implementation and complex work, with thinking adjusted by task ambiguity.

The executable model, thinking, and fallback choices are in [Pi model profiles](../../../pi/model-profiles.json). Select the tier by the main deliverable and the task's uncertainty; an explicit user choice takes precedence. Pass the selected model and thinking level to each Pi dispatch.
