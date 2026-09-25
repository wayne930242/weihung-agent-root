# claude-drive-codex

Opus 5.5 coordinates and implements; Codex Luna writes documents and investigates, Sol handles UI, review, and clear complex work, and Astra handles ambiguous complex work and research.

Created: 2026-09-07.
Updated: 2026-09-25.
Rationale: The user asked to align this strategy with drive-all and replace the agy tier with Codex's low-tier model. OpenAI's Codex model guide positions GPT-6 Luna as the lowest-cost GPT-6 model for clear, repeatable work such as extraction, transformation, and structured summaries. This strategy keeps drive-all's medium effort for that tier. On 2026-09-23 the user raised documentation to Luna high and UI/UX work to Sol medium; investigation and data processing stay on Luna medium, and routine inspection stays on Sol low. The user then moved complex work with clear instructions to Sol high and complex work with unclear instructions to Astra low, reserving Astra high for academic research and forward-looking hard problems. On 2026-09-24 the user retired Sonnet and moved implementation to Opus 5.5: low for simple work, medium for standard work. On 2026-09-25 the user kept Opus 5.5 1M only for main coordination and complex work; other Opus tiers use the bridge's 200K twin `claude-bridge/claude-200k-opus-5-5`, and a Luna tier falls back to Haiku 4.5 rather than Opus.

## Pi tiers

| Tier | Model | Thinking |
|---|---|---|
| main | `claude-bridge/claude-opus-5-5` | high |
| docs | `openai-codex/gpt-6-luna` | high |
| recon | `openai-codex/gpt-6-luna` | medium |
| ui | `openai-codex/gpt-6-sol` | medium |
| review | `openai-codex/gpt-6-sol` | low |
| simple | `claude-bridge/claude-200k-opus-5-5` | low |
| coding | `claude-bridge/claude-200k-opus-5-5` | medium |
| complex_clear | `openai-codex/gpt-6-sol` | high |
| complex_unclear | `openai-codex/gpt-6-astra` | low |
| academic | `openai-codex/gpt-6-astra` | high |

Opus 5.5 stays with main coordination and ordinary implementation. Luna handles documentation and investigation; Sol handles UI and routine review; Sol high and Astra low separate predictable instructions from ambiguous complex work. Astra high remains reserved for research.

[pi/model-profiles.json](../../../pi/model-profiles.json) holds the executable values; the table mirrors it. Choose the tier with the tier guide in [model-preference-profile.md](../model-preference-profile.md).
