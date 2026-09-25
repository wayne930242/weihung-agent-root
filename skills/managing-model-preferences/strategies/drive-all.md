# drive-all

Multi-harness dispatch across Antigravity, Claude, and Codex: agy-medium for documentation, investigation, and source data cleaning and processing, Claude Opus 5.5 for implementation (low for simple, medium for standard and large code work), Codex sol-medium for UI/UX, Codex sol-low for routine review, Codex sol-high for complex work with clear instructions, Codex astra-low for complex work with unclear instructions, and Codex astra-high for academic research and forward-looking hard problems.

Created: 2026-09-14.
Updated: 2026-09-24.
Rationale: The user configured a multi-harness profile (drive-all): documentation, investigation, and source data cleaning and processing use agy-medium, simple implementation uses Claude sonnet low, standard implementation uses Claude sonnet high, UI/UX and routine review use Codex sol-low. The user then defined complexity as environmental unpredictability rather than code volume: large code work stays on Claude sonnet high, complex work uses Codex astra-low, and only complex work whose instructions are unclear and situation ambiguous uses Codex astra-high. On 2026-09-24 the user retired Sonnet and moved implementation to Opus 5.5: low for simple work, medium for standard work. The user also aligned the Codex tiers with claude-drive-codex: UI/UX on Sol medium, routine review on Sol low, complex work with clear instructions on Sol high, complex work with unclear instructions on Astra low, and Astra high reserved for academic research and forward-looking hard problems.

## Pi tier rationale

The former Gemini and agy document and investigation tier maps to Codex Luna medium, following the confirmed Pi migration choice. Opus remains the implementation tier; Sol and Astra retain their UI, review, and complex-work roles.

The executable model, thinking, and fallback choices are in [Pi model profiles](../../../pi/model-profiles.json). Select the tier by the main deliverable and the task's uncertainty; an explicit user choice takes precedence. Pass the selected model and thinking level to each Pi dispatch.
