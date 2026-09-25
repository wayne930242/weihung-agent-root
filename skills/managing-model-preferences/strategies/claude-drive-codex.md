# claude-drive-codex

Claude-coordinated dispatch across Claude and Codex with no Antigravity usage: Opus 5.5 high for main coordination, Codex luna-high for documentation, Codex luna-medium for investigation and source data cleaning and processing, Claude Opus 5.5 for implementation (low for simple, medium for standard and large code work), Codex sol-medium for UI/UX, Codex sol-low for routine review, Codex sol-high for complex work with clear instructions, Codex astra-low for complex work with unclear instructions, and Codex astra-high for academic research and forward-looking hard problems.

Created: 2026-09-07.
Updated: 2026-09-24.
Rationale: The user asked to align this strategy with drive-all and replace the agy tier with Codex's low-tier model. OpenAI's Codex model guide positions GPT-6 Luna as the lowest-cost GPT-6 model for clear, repeatable work such as extraction, transformation, and structured summaries. This strategy keeps drive-all's medium effort for that tier. On 2026-09-23 the user raised documentation to Luna high and UI/UX work to Sol medium; investigation and data processing stay on Luna medium, and routine inspection stays on Sol low. The user then moved complex work with clear instructions to Sol high and complex work with unclear instructions to Astra low, reserving Astra high for academic research and forward-looking hard problems. On 2026-09-24 the user retired Sonnet and moved implementation to Opus 5.5: low for simple work, medium for standard work.

## Pi tier rationale

Opus 5.5 stays with main coordination and ordinary implementation. Luna handles documentation and investigation; Sol handles UI and routine review; Sol high and Astra low separate predictable instructions from ambiguous complex work. Astra high remains reserved for research.

The executable model, thinking, and fallback choices are in [Pi model profiles](../../../pi/model-profiles.json). Select the tier by the main deliverable and the task's uncertainty; an explicit user choice takes precedence. Pass the selected model and thinking level to each Pi dispatch.
