# Use Opus as the Claude main model verification

## Requirement evidence

| Requirement | Evidence | Result |
|---|---|---|
| Repository settings contain Opus main, cross-session accept, no advisor, and no worker pin | `python3 -m json.tool config/claude-settings.json` parsed successfully; direct `jq` inspection reported `model=opus`, no `advisorModel`, `crossSessionInbound=accept`, and no worker pin | pass |
| Fresh install writes Opus main without advisor or worker overrides | `bash tests/install.sh`; `fresh_install_manages_explicit_model_settings` and the fresh managed-surface case inspected fake-home settings through the public installer | pass |
| Upgrade replaces Sonnet main and removes the former Opus advisor | `bash tests/install.sh`; `former_managed_opus_advisor_is_removed_on_upgrade` started with `model=sonnet` and `advisorModel=opus`, then observed `model=opus` and no advisor | pass |
| Current documentation describes Opus main without a repository-managed advisor | Static inspection of `README.md` and installer help; active-source search found advisor references only in migration and preservation tests | pass |
| Real user-root settings match repository model settings | `bash scripts/install.sh` reported the former advisor migration; direct source/installed `jq` inspection reported `model=opus`, no advisor, `crossSessionInbound=accept`, and no worker pin in both | pass |
| Legacy Sonnet worker migration remains value-sensitive | Full install suite passed legacy Sonnet removal, empty/mixed environment, custom worker, and non-object environment cases | pass |
| A user-selected non-Opus advisor survives installation | `user_selected_advisor_survives_install` and the mixed legacy-worker case observed the custom advisor unchanged | pass |
| Uninstall removes only the managed Opus main and preserves user model/advisor values | Full `bash tests/uninstall.sh`; fresh uninstall and `uninstall_keeps_user_model_preferences` passed through the public uninstall interface | pass |
| Existing hooks, cross-session behavior, Codex roles, and managed links remain intact | Full install/uninstall suites passed; the real installer reported every existing managed link as `OK`; focused link checks resolved the main Claude/Codex prompts, hooks, and Codex roles | pass |

## TDD evidence

- Red: the fresh-install, former-advisor upgrade, and custom-advisor preservation
  cases all failed against the previous Sonnet/Opus implementation for their
  expected setting mismatches.
- Green: all three focused cases plus the combined legacy-worker migration case
  passed after the settings and migration changes.
- Regression: complete `bash tests/install.sh` and `bash tests/uninstall.sh`
  suites both exited 0.

## Additional validation

- `bash -n scripts/install.sh scripts/uninstall.sh tests/install.sh tests/uninstall.sh` passed.
- Both Claude JSON fragments parsed with `python3 -m json.tool`.
- `git diff --check` passed before the real installation.
- `claude doctor` reported native Claude Code 2.1.251 with no installation issues.
- A second real installer run emitted no migration event and left Opus main,
  no advisor, and no worker pin unchanged.
- No user or project `settings.local.json` was present in the inspected active
  settings locations to override the removed advisor.

## Human appropriateness

The user explicitly approved Opus as the main model and removal of the advisor.

## Deviations

None.

## Unresolved gaps

None for the approved repository and local-install scope. The changes are not
committed or pushed because neither action was authorized.
