---
name: managing-model-preferences
description: Manage model preference strategies for this project. Use when viewing the active strategy, adding or switching strategies, or adjusting model tiers, dispatch priority, and effort levels.
argument-hint: "[strategy name | status | preference to add or revise]"
---

# Managing Model Preferences

Route the request's argument first:

- None, `status`, or `list`: read [model-preference-profile.md](model-preference-profile.md) and [Pi model profiles](../../pi/model-profiles.json); report the active strategy, its activation date, rationale, exact Pi tiers, and the other strategies in the catalog. This branch is read-only and ends here.
- A strategy name from the catalog: switch to it through steps 1, 3, and 4, changing only the entrypoint's active link, date, and rationale.
- A new or adjusted preference: run steps 1 through 4.

1. Read [model-preference-profile.md](model-preference-profile.md) in this directory, then read the currently active strategy and any requested strategy for rationale. Read [Pi model profiles](../../pi/model-profiles.json) for exact model and thinking tiers. Standard Pi dispatch reads the active strategy from the entrypoint and its tier from the JSON map.
   Completion criteria: Explain the difference between currently active rules and requested changes.
2. Determine updates based on stated user preferences. If an unresolved choice alters the model or effort, ask one question at a time. Verify model identifiers and effort parameters against the current harness model list, CLI help, or official documentation, distinguishing preference names from actual CLI arguments.
   Completion criteria: Each tier has an explicit model, effort, and verified parameter reference; unsupported settings are reported.
3. Continue authorized modifications through `aaaav-do`. Resolve the actual source directory of this skill and operate in the source checkout: write new strategy rationale to `strategies/<name>.md`, put Pi model and thinking tiers in `pi/model-profiles.json`, and register the strategy in the index; update the entrypoint link, date, and rationale for strategy switches. The user's current judgment serves as the preference rationale. When Pi is installed, run `python3 scripts/pi-target.py apply-profile --home "$HOME"` from this repository and reload Pi so the new default model and `pi-herdr-agents` routing take effect.
   Completion criteria: The entrypoint specifies one active strategy; Pi settings reflect that strategy; Git diff verifies the additions, revisions, or switches. When the user requests version control, perform a scoped commit after verification and report the commit; push only when authorized.
4. Verify the active strategy and dispatch parameters. In the source checkout, run `bash tests/prompts.sh`, `bash tests/install.sh`, and `bash tests/uninstall.sh`. For Pi, also run `node --experimental-strip-types tests/pi-dispatch.mjs` and inspect the installed `~/.pi/agent/settings.json` and `~/.pi/agent/herdr-agents/config.json` after applying the profile. Walk through simple, standard, complex, zero-defect, and explicit override scenarios.
   Completion criteria: Report selection results across scenarios, distinguishing local validation, installation, and real dispatch evidence.
