---
name: managing-model-preferences
description: Manage model preference strategies for this project. Use when viewing the active strategy, adding or switching strategies, or adjusting model tiers, dispatch priority, and thinking levels.
argument-hint: "[strategy name | status | preference to add or revise]"
---

# Managing Model Preferences

Route the request's argument first:

- None, `status`, or `list`: read [model-preference-profile.md](model-preference-profile.md), its active strategy, and [Pi model profiles](../../pi/model-profiles.json); report the active strategy, activation date, rationale, its pi tiers, and the other strategies in the catalog. This branch is read-only and ends here.
- A strategy name from the catalog: switch to it through steps 1, 3, and 4, changing only the entrypoint's active link, date, and rationale.
- A new or adjusted preference: run steps 1 through 4.

1. Read [model-preference-profile.md](model-preference-profile.md) in this directory, then the currently active strategy and any requested strategy, and their entries in [Pi model profiles](../../pi/model-profiles.json).
   Completion criteria: Explain the difference between currently active rules and requested changes.
2. Determine updates based on stated user preferences. If an unresolved choice alters a model or thinking level, ask one question at a time. Verify each `provider/model-id` and thinking level against `pi --list-models` or the pi documentation.
   Completion criteria: Each tier has an explicit model and thinking level that pi accepts; unsupported settings are reported.
3. Continue authorized modifications through `aaaav-do`. Resolve the actual source directory of this skill and operate in the source checkout: put the executable tiers in `pi/model-profiles.json`, mirror them in the tier table of `strategies/<name>.md` with the user's current judgment as its rationale, and register a new strategy in the entrypoint's table; a switch updates the entrypoint link, date, and rationale. Then run `python3 scripts/pi-target.py apply-profile --home "$HOME"` from the repository and reload pi so the new default model and `pi-herdr-agents` routing take effect.
   Completion criteria: The entrypoint names one active strategy; pi settings reflect it; the Git diff shows the additions, revisions, or switch. When the user requests version control, commit after verification and report the commit; push only when authorized.
4. In the source checkout, run `python3 tests/pi_review_fixes.py` and `bash tests/install.sh`. Inspect `~/.pi/agent/settings.json`, `~/.pi/agent/herdr-agents/config.json`, and the model strategy section of `~/.pi/agent/AGENTS.md`. Walk through simple, standard, complex, academic, and explicit override scenarios with the tier guide.
   Completion criteria: Report the selected tier and model for each scenario, distinguishing local test, installation, and real dispatch evidence.
