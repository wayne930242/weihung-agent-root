# codex-first

Prefer Codex for delegated non-implementation work with the same tiers as claude-drive-codex: Codex luna-high for documentation, Codex luna-medium for investigation and source data cleaning and processing, Codex sol-medium for UI/UX, Codex sol-low for routine review, Claude Opus 5.5 for implementation (low for simple, medium for standard and large code work), Codex sol-high for complex work with clear instructions, Codex astra-low for complex work with unclear instructions, and Codex astra-high for academic research and forward-looking hard problems.

Created: 2026-09-07.
Updated: 2026-09-24.
Rationale: The user requested lower Astra spending, Luna high for documentation, Sol high for investigation, Astra low for simple implementation, and Astra high for complex work.
On 2026-09-24 the user aligned this strategy with claude-drive-codex: investigation moves to Luna medium, routine review to Sol low, UI/UX to Sol medium, implementation to Claude Opus 5.5 low and medium, complex work to Sol high or Astra low by instruction clarity, and Astra high is reserved for academic research and forward-looking hard problems.

## Pi tier rationale

The main Pi session uses Sol high. Implementation remains on Opus low or medium, while Luna and Sol cover documentation, investigation, UI, and review. Astra is reserved for ambiguous complex work and academic research.

The executable model, thinking, and fallback choices are in [Pi model profiles](../../../pi/model-profiles.json). Select the tier by the main deliverable and the task's uncertainty; an explicit user choice takes precedence. Pass the selected model and thinking level to each Pi dispatch.
