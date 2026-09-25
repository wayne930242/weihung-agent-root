# codex-first

The claude-drive-codex tiers under a Codex Sol high main session, kept as a separate entry for its own history.

Created: 2026-09-07.
Updated: 2026-09-24.
Rationale: The user requested lower Astra spending, Luna high for documentation, Sol high for investigation, Astra low for simple implementation, and Astra high for complex work.
On 2026-09-24 the user aligned this strategy with claude-drive-codex: investigation moves to Luna medium, routine review to Sol low, UI/UX to Sol medium, implementation to Claude Opus 5.5 low and medium, complex work to Sol high or Astra low by instruction clarity, and Astra high is reserved for academic research and forward-looking hard problems.

## Pi tiers

| Tier | Model | Thinking |
|---|---|---|
| main | `openai-codex/gpt-6-sol` | high |
| docs | `openai-codex/gpt-6-luna` | high |
| recon | `openai-codex/gpt-6-luna` | medium |
| ui | `openai-codex/gpt-6-sol` | medium |
| review | `openai-codex/gpt-6-sol` | low |
| simple | `claude-bridge/claude-opus-5-5` | low |
| coding | `claude-bridge/claude-opus-5-5` | medium |
| complex_clear | `openai-codex/gpt-6-sol` | high |
| complex_unclear | `openai-codex/gpt-6-astra` | low |
| academic | `openai-codex/gpt-6-astra` | high |

The main Pi session uses Sol high. Implementation remains on Opus low or medium, while Luna and Sol cover documentation, investigation, UI, and review. Astra is reserved for ambiguous complex work and academic research.

[pi/model-profiles.json](../../../pi/model-profiles.json) holds the executable values; the table mirrors it. Choose the tier with the tier guide in [model-preference-profile.md](../model-preference-profile.md).
