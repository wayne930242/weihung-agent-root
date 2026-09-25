# drive-all

The claude-drive-codex tiers with documents on Luna medium, the tier that replaced the former agy lightweight tier.

Created: 2026-09-14.
Updated: 2026-09-25.
Rationale: The user configured a multi-harness profile (drive-all): documentation, investigation, and source data cleaning and processing use agy-medium, simple implementation uses Claude sonnet low, standard implementation uses Claude sonnet high, UI/UX and routine review use Codex sol-low. The user then defined complexity as environmental unpredictability rather than code volume: large code work stays on Claude sonnet high, complex work uses Codex astra-low, and only complex work whose instructions are unclear and situation ambiguous uses Codex astra-high. On 2026-09-24 the user retired Sonnet and moved implementation to Opus 5.5: low for simple work, medium for standard work. The user also aligned the Codex tiers with claude-drive-codex: UI/UX on Sol medium, routine review on Sol low, complex work with clear instructions on Sol high, complex work with unclear instructions on Astra low, and Astra high reserved for academic research and forward-looking hard problems. On 2026-09-25 the user kept Opus 5.5 1M only for main coordination and complex work; other Opus tiers use the bridge's 200K twin `claude-bridge/claude-200k-opus-5-5`, and a Luna tier falls back to Haiku 4.5 rather than Opus.

## Pi tiers

| Tier | Model | Thinking |
|---|---|---|
| main | `claude-bridge/claude-opus-5-5` | high |
| docs | `openai-codex/gpt-6-luna` | medium |
| recon | `openai-codex/gpt-6-luna` | medium |
| ui | `openai-codex/gpt-6-sol` | medium |
| review | `openai-codex/gpt-6-sol` | low |
| simple | `claude-bridge/claude-200k-opus-5-5` | low |
| coding | `claude-bridge/claude-200k-opus-5-5` | medium |
| complex_clear | `openai-codex/gpt-6-sol` | high |
| complex_unclear | `openai-codex/gpt-6-astra` | low |
| academic | `openai-codex/gpt-6-astra` | high |

The former Gemini and agy document and investigation tier maps to Codex Luna medium, following the confirmed Pi migration choice. Opus remains the implementation tier; Sol and Astra retain their UI, review, and complex-work roles.

[pi/model-profiles.json](../../../pi/model-profiles.json) holds the executable values; the table mirrors it. Choose the tier with the tier guide in [model-preference-profile.md](../model-preference-profile.md).
