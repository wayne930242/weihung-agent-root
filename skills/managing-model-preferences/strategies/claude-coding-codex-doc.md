# claude-coding-codex-doc

Opus 5.5 for coding, investigation, and review; Codex Luna for documents and Sol for UI.

Created: 2026-09-07.
Updated: 2026-09-25.
Rationale: The user saved the model split used before the model preference profile existed: Opus for coding, investigation, and lookup, and Codex for documents with an explicit model for UI/UX review. On 2026-09-24 the user retired Sonnet and moved coding, investigation, and queries to Opus 5.5 medium. On 2026-09-25 the user kept Opus 5.5 1M only for main coordination and complex work; other Opus tiers use the bridge's 200K twin `claude-bridge/claude-200k-opus-5-5`, and a Luna tier falls back to Haiku 4.5 rather than Opus.

## Pi tiers

| Tier | Model | Thinking |
|---|---|---|
| main | `claude-bridge/claude-opus-5-5` | high |
| docs | `openai-codex/gpt-6-luna` | high |
| recon | `claude-bridge/claude-200k-opus-5-5` | medium |
| ui | `openai-codex/gpt-6-sol` | medium |
| review | `claude-bridge/claude-200k-opus-5-5` | medium |
| simple | `claude-bridge/claude-200k-opus-5-5` | medium |
| coding | `claude-bridge/claude-200k-opus-5-5` | medium |
| complex_clear | `claude-bridge/claude-opus-5-5` | xhigh |
| complex_unclear | `claude-bridge/claude-opus-5-5` | xhigh |
| academic | `claude-bridge/claude-opus-5-5` | xhigh |

Opus remains the coding and investigation model. Codex Luna handles documentation, and Sol handles UI review. This preserves the original division while giving Pi exact model and thinking values.

[pi/model-profiles.json](../../../pi/model-profiles.json) holds the executable values; the table mirrors it. Choose the tier with the tier guide in [model-preference-profile.md](../model-preference-profile.md).
