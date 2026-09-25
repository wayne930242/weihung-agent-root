# claude-with-agy

Codex-light routing: Luna medium covers documents, investigation, UI, and review, which were the former agy tier; Opus 5.5 covers implementation and all complex work.

Created: 2026-09-15.
Updated: 2026-09-24.
Rationale: The user requested a drive-all variant that consumes no Codex tokens: Astra low becomes Claude opus[1m] and Astra high becomes Claude Fable 5.1, each keeping its effort level, and the user chose agy-medium to replace Codex sol-low for UI/UX and routine review, keeping a non-Claude review perspective. On 2026-09-23 the user replaced Fable 5.1 high with Opus 5.5 1M xhigh and pinned Opus to 5.5. On 2026-09-24 the user retired Sonnet and moved implementation to Opus 5.5: low for simple work, medium for standard work.

## Pi tiers

| Tier | Model | Thinking |
|---|---|---|
| main | `claude-bridge/claude-opus-5-5` | high |
| docs | `openai-codex/gpt-6-luna` | medium |
| recon | `openai-codex/gpt-6-luna` | medium |
| ui | `openai-codex/gpt-6-luna` | medium |
| review | `openai-codex/gpt-6-luna` | medium |
| simple | `claude-bridge/claude-opus-5-5` | low |
| coding | `claude-bridge/claude-opus-5-5` | medium |
| complex_clear | `claude-bridge/claude-opus-5-5` | low |
| complex_unclear | `claude-bridge/claude-opus-5-5` | xhigh |
| academic | `claude-bridge/claude-opus-5-5` | xhigh |

The former Gemini and agy lightweight tiers map to Codex Luna medium, following the confirmed Pi migration choice. Opus handles implementation and complex work, with thinking adjusted by task ambiguity.

[pi/model-profiles.json](../../../pi/model-profiles.json) holds the executable values; the table mirrors it. Choose the tier with the tier guide in [model-preference-profile.md](../model-preference-profile.md).
