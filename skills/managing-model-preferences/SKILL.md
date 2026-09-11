---
name: managing-model-preferences
description: Manage model preference strategies for this project. Use when adding or switching strategies, or adjusting model tiers, dispatch priority, and effort levels.
---

# Managing Model Preferences

1. Read [model-preference-profile.md](model-preference-profile.md) in this directory, then read the currently active strategy and any requested strategy to confirm the selection order and effort tiers. Standard dispatch reads the active strategy from the entrypoint.
   Completion criteria: Explain the difference between currently active rules and requested changes.
2. Determine updates based on stated user preferences. If an unresolved choice alters the model or effort, ask one question at a time. Verify model identifiers and effort parameters against the current harness model list, CLI help, or official documentation, distinguishing preference names from actual CLI arguments.
   Completion criteria: Each tier has an explicit model, effort, and verified parameter reference; unsupported settings are reported.
3. Continue authorized modifications through `aaaav-do`. Resolve the actual source directory of this skill and operate in the source checkout: write new strategies to `strategies/<name>.md` and register them in the index; update existing strategy files for revisions; update the entrypoint link, date, and rationale for strategy switches. The user's current judgment serves as the preference rationale.
   Completion criteria: Strategies are stored individually, while the entrypoint specifies the single active strategy; Git diff verifies the additions, revisions, or switches. When the user requests version control, perform a scoped commit after verification and report the commit; push only when authorized.
4. Verify entrypoints and dispatch parameters for Claude and Codex. In the source checkout, run `bash tests/prompts.sh`, `bash tests/install.sh`, and `bash tests/uninstall.sh`. Walk through simple, standard, complex, zero-defect, and explicit override scenarios.
   Completion criteria: Report selection results across scenarios, distinguishing local validation, installation, and real dispatch evidence.
