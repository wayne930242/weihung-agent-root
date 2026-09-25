# claude-coding-codex-doc

Saved: 2026-09-07.
Updated: 2026-09-24. The user retired Sonnet and moved coding, investigation, and queries to Opus 5.5 medium.
Source: the model split in CLAUDE.md before this migration, including the workspace's explicit UI/UX model choice.

## Pi tier rationale

Opus remains the coding and investigation model. Codex Luna handles documentation, and Sol handles UI review. This preserves the original division while giving Pi exact model and thinking values.

The executable model, thinking, and fallback choices are in [Pi model profiles](../../../pi/model-profiles.json). Select the tier by the main deliverable and the task's uncertainty; an explicit user choice takes precedence. Pass the selected model and thinking level to each Pi dispatch.
