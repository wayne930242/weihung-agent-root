# claude-only

Opus 5.5 for every tier, with thinking from low for bounded work to xhigh for ambiguous complex work.

Created: 2026-09-07.
Updated: 2026-09-25.
Rationale: The user initially chose this profile when Codex quota was nearly exhausted. Later revisions separated complex work by environmental uncertainty, moved Fable's ambiguous tier to Opus 5.5 xhigh, raised main coordination to high, and retired Sonnet. During Pi migration, the user selected the upstream bridge commit that measures Opus 5.5 at 1M on Max and exposes that window in Pi. On 2026-09-25 the user kept Opus 5.5 1M only for main coordination and complex work; other Opus tiers use the bridge's 200K twin `claude-bridge/claude-200k-opus-5-5`, and a Luna tier falls back to Haiku 4.5 rather than Opus.

## Pi tiers

| Tier | Model | Thinking |
|---|---|---|
| main | `claude-bridge/claude-opus-5-5` | high |
| docs | `claude-bridge/claude-200k-opus-5-5` | medium |
| recon | `claude-bridge/claude-200k-opus-5-5` | low |
| ui | `claude-bridge/claude-200k-opus-5-5` | low |
| review | `claude-bridge/claude-200k-opus-5-5` | medium |
| simple | `claude-bridge/claude-200k-opus-5-5` | low |
| coding | `claude-bridge/claude-200k-opus-5-5` | medium |
| complex_clear | `claude-bridge/claude-opus-5-5` | low |
| complex_unclear | `claude-bridge/claude-opus-5-5` | xhigh |
| academic | `claude-bridge/claude-opus-5-5` | xhigh |

Opus remains the preferred model for every tier. Pi keeps a Codex fallback for bridge outages, as required by the migration contract. Thinking ranges from low for bounded work to xhigh for ambiguous complex work.

[pi/model-profiles.json](../../../pi/model-profiles.json) holds the executable values; the table mirrors it. Choose the tier with the tier guide in [model-preference-profile.md](../model-preference-profile.md).
