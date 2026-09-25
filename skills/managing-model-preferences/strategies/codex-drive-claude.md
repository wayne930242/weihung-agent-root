# codex-drive-claude

Codex-coordinated dispatch with the same tiers as claude-drive-codex: a Codex main session for coordination, Codex luna-high for documentation, Codex luna-medium for investigation and source data cleaning and processing, Codex sol-medium for UI/UX, Codex sol-low for routine review, Claude Opus 5.5 for implementation (low for simple, medium for standard and large code work), Codex sol-high for complex work with clear instructions, Codex astra-low for complex work with unclear instructions, and Codex astra-high for academic research and forward-looking hard problems.

Created: 2026-09-07.
Updated: 2026-09-24.
Rationale: The user originally assigned light work to Claude Sonnet, complex work to Opus 5.5, and documentation alone to low-effort Codex.
On 2026-09-24 the user retired Sonnet and aligned this strategy with claude-drive-codex; only main coordination differs, running in a Codex session.

## Pi tier rationale

The main Pi session uses Sol high while implementation keeps Opus low or medium. Luna handles documents and investigation; Sol handles UI and review. Complex work follows the same Sol and Astra split as claude-drive-codex.

The executable model, thinking, and fallback choices are in [Pi model profiles](../../../pi/model-profiles.json). Select the tier by the main deliverable and the task's uncertainty; an explicit user choice takes precedence. Pass the selected model and thinking level to each Pi dispatch.
