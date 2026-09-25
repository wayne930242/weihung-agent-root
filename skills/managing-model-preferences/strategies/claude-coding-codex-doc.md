# claude-coding-codex-doc

Saved: 2026-09-07.
Updated: 2026-09-24. The user retired Sonnet and moved coding, investigation, and queries to Opus 5.5 medium.
Source: the model split in CLAUDE.md before this migration, including the workspace's explicit UI/UX model choice.

## Selection order

Apply the user's explicit model and effort choice first. For other work:

1. The most complex delegated work uses the current main agent model.
2. Delegate document writing to `codex`.
3. Use Claude `claude-opus-5-5` at `medium` effort for coding, investigation, and lookup.
4. Other work uses the current main agent model.

The main agent handles simple direct requests. Use Straw Boss for work that needs an independent workroom and a subagent for a self-contained fragment.

## Dedicated choices

| Work | Selection |
|---|---|
| Write or substantially revise an article | Codex `gpt-6-sol`; inherit configured effort |
| Translate, format, or extract data mechanically | Codex `gpt-6-luna` at `low` effort |
| Review or revise a new UI/UX design | Explicit Codex model, at least `gpt-6-sol`; inherit configured effort |
| Other Codex documentation work | Inherit the configured Codex model and effort |

An Opus main agent may hand extremely complex work to `claude-opus-5-5[1m]` at `xhigh` effort through the Straw Boss `handoff-orchestrator` and `i-am-orchestrator` flows.

## Application

Confirm inherited models and effort against the current harness before reactivating this legacy strategy. Resolve actual values and pass them explicitly in dispatch parameters. Report an unavailable combination for the user's replacement choice.

## Pi tier rationale

Opus remains the coding and investigation model. Codex Luna handles documentation, and Sol handles UI review. This preserves the original division while giving Pi exact model and thinking values.

The executable model, thinking, and fallback choices are in [Pi model profiles](../../../pi/model-profiles.json). Select the tier by the main deliverable and the task's uncertainty; an explicit user choice takes precedence. Pass the selected model and thinking level to each Pi dispatch.
