# codex-drive-claude

The claude-drive-codex tiers under a Codex Sol high main session.

Created: 2026-09-07.
Updated: 2026-09-25.
Rationale: The user originally assigned light work to Claude Sonnet, complex work to Opus 5.5, and documentation alone to low-effort Codex. On 2026-09-25 the user kept Opus 5.5 1M only for main coordination and complex work; other Opus tiers use the bridge's 200K twin `claude-bridge/claude-200k-opus-5-5`, and a Luna tier falls back to Haiku 4.5 rather than Opus.
On 2026-09-24 the user retired Sonnet and aligned this strategy with claude-drive-codex; only main coordination differs, running in a Codex session.

## Pi tiers

| Tier | Model | Thinking |
|---|---|---|
| main | `openai-codex/gpt-6-sol` | high |
| docs | `openai-codex/gpt-6-luna` | high |
| recon | `openai-codex/gpt-6-luna` | medium |
| ui | `openai-codex/gpt-6-sol` | medium |
| review | `openai-codex/gpt-6-sol` | low |
| simple | `claude-bridge/claude-200k-opus-5-5` | low |
| coding | `claude-bridge/claude-200k-opus-5-5` | medium |
| complex_clear | `openai-codex/gpt-6-sol` | high |
| complex_unclear | `openai-codex/gpt-6-astra` | low |
| academic | `openai-codex/gpt-6-astra` | high |

The main Pi session uses Sol high while implementation keeps Opus low or medium. Luna handles documents and investigation; Sol handles UI and review. Complex work follows the same Sol and Astra split as claude-drive-codex.

[pi/model-profiles.json](../../../pi/model-profiles.json) holds the executable values; the table mirrors it. Choose the tier with the tier guide in [model-preference-profile.md](../model-preference-profile.md).
