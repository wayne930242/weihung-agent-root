# claude-drive-codex

Opus 5.5 1M coordinates and Sonnet 5.5 implements; Opus 5.5 200K handles ambiguous complex work, planning, and research; Codex Luna writes documents and investigates, Sol handles review and clear complex work, and Astra handles UI.

Created: 2026-09-07.
Updated: 2026-10-02.
Rationale: The user asked to align this strategy with drive-all and replace the agy tier with Codex's low-tier model. OpenAI's Codex model guide positions GPT-6 Luna as the lowest-cost GPT-6 model for clear, repeatable work such as extraction, transformation, and structured summaries. This strategy keeps drive-all's medium effort for that tier. On 2026-09-23 the user raised documentation to Luna high and UI/UX work to Sol medium; investigation and data processing stay on Luna medium, and routine inspection stays on Sol low. The user then moved complex work with clear instructions to Sol high and complex work with unclear instructions to Astra low, reserving Astra high for academic research and forward-looking hard problems. On 2026-09-24 the user retired Sonnet and moved implementation to Opus 5.5: low for simple work, medium for standard work. On 2026-09-25 the user kept Opus 5.5 1M only for main coordination and complex work; other Opus tiers use the bridge's 200K twin `claude-bridge/claude-200k-opus-5-5`, and a Luna tier falls back to Haiku 4.5 rather than Opus. On 2026-09-29, with Sonnet 5.5 released, the user moved implementation from Opus to Sonnet 5.5 (`claude-bridge/claude-sonnet-5-5`, registered at 200K by the bridge until pi-ai's catalog lists it), raising thinking one level to medium for simple work and high for standard work to offset the smaller model. The same day the user moved UI/UX design and review from Sol to Astra (`openai-codex/gpt-6-astra`), keeping medium thinking. Later that day, finding Codex used too rarely in practice, the user raised routine review to Sol high. The user then lowered main coordination to Opus 5.5 medium: Anthropic sets medium as the Opus 5.5 default and recommends high where verification and edge cases dominate, and with the user in the loop and review on Sol high, main coordination fits medium; raise a session to high manually for production operations or hard debugging. On 2026-09-30 the user moved main coordination to Sonnet 5.5 1M (`claude-bridge/claude-sonnet-5-5`) high, reserving Opus for hard thinking: complex work with unclear instructions, which also serves `task:architecture` planning and diagnosis, moved to Opus 5.5 200K high, and academic research to Opus 5.5 200K xhigh. Codex keeps documentation, investigation, UI, review, and clear complex work; the user accepts lower Codex usage and plans to keep only the $20 Codex plan, so Claude carries the main load. On 2026-10-02 the user moved main coordination back to Opus 5.5 1M (`claude-bridge/claude-opus-5-5`) medium; Anthropic sets medium as the Opus 5.5 default, and raise a session to high manually for production operations or hard debugging. Main falls back to Sol; complex tiers fall back to Astra.

## Pi tiers

| Tier | Model | Thinking |
|---|---|---|
| main | `claude-bridge/claude-opus-5-5` | medium |
| docs | `openai-codex/gpt-6-luna` | high |
| recon | `openai-codex/gpt-6-luna` | medium |
| ui | `openai-codex/gpt-6-astra` | medium |
| review | `openai-codex/gpt-6.1-sol` | high |
| simple | `claude-bridge/claude-sonnet-5-5` | medium |
| coding | `claude-bridge/claude-sonnet-5-5` | high |
| complex_clear | `openai-codex/gpt-6.1-sol` | high |
| complex_unclear | `claude-bridge/claude-200k-opus-5-5` | high |
| academic | `claude-bridge/claude-200k-opus-5-5` | xhigh |

Opus 5.5 1M medium handles main coordination; Sonnet 5.5 handles ordinary implementation. Luna handles documentation and investigation; Astra medium handles UI; Sol high handles routine review and complex work with clear instructions. Opus 5.5 200K high takes ambiguous complex work and planning, and xhigh is reserved for research.

[pi/model-profiles.json](../../../pi/model-profiles.json) holds the executable values; the table mirrors it. Choose the tier with the tier guide in [model-preference-profile.md](../model-preference-profile.md).
