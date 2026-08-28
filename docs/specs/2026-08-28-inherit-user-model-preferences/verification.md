# Inherit user model preferences verification

## Requirement evidence

| Requirement | Evidence | Result |
|---|---|---|
| Fresh install writes no main, advisor, or worker model selection | `bash tests/install.sh`; `fresh_install_inherits_model_settings` inspected the settings produced through the public installer | pass |
| Upgrade removes the former `sonnet` worker pin and removes an emptied `env` object | `bash tests/install.sh`; `legacy_worker_pin_is_removed_without_touching_user_preferences` and `legacy_only_worker_pin_removes_empty_env` | pass |
| Install preserves user main, advisor, non-Sonnet worker, and unrelated environment values | `bash tests/install.sh`; migration and user-selected-worker cases inspected all named values | pass |
| Current documentation and agent definitions contain no active main, advisor, or worker model recommendation or pin | Agent diff review and exact `model =` search across active Claude/Codex sources; remaining `sonnet` references are explicitly legacy migration/test values | pass |
| Real installation removes the old worker pin and preserves the existing advisor preference | Before/after inspection around `bash scripts/install.sh`: `advisorModel` remained `opus`; `CLAUDE_CODE_SUBAGENT_MODEL` changed from `sonnet` to absent | pass |
| Missing or non-object `env` does not break installation | `bash tests/install.sh`; fresh-install and `non_object_env_does_not_break_install` cases | pass |
| A mixed `env` object loses only the legacy worker pin | `bash tests/install.sh`; migration case retained `USER_ENV=keep-me` | pass |
| A user-selected non-Sonnet worker value survives install and uninstall | `bash tests/install.sh` and `bash tests/uninstall.sh`; both public script suites inspected `user-worker-model` | pass |
| Existing Claude/Codex managed surfaces remain operational | Full install and uninstall suites passed; real install reported existing managed links as OK; direct resolution confirmed prompt links and installed Codex agent definitions | pass |
| Migration is value-sensitive and does not repeat | User-worker preservation test passed; a second real installer run emitted no migration event and left the worker pin absent | pass |

## TDD evidence

- Red: before production changes, all three initial focused cases failed for the
  expected reason: the current settings fragment installed or retained
  `CLAUDE_CODE_SUBAGENT_MODEL=sonnet`.
- Red: the installed Codex-agent check then failed on the existing
  `model = "gpt-5.4-mini"` override before both Codex model overrides were
  removed. An earlier attempt using unavailable `tomllib` was discarded and
  replaced with a dependency-free exact-key check.
- Green: after removing the pin and adding the upgrade migration, the focused
  install cases and user-preference uninstall case passed.
- Regression: full `bash tests/install.sh` and `bash tests/uninstall.sh` runs
  both exited 0.

## Additional validation

- `bash -n scripts/install.sh scripts/uninstall.sh tests/install.sh tests/uninstall.sh`
  passed.
- `python3 -m json.tool` parsed both Claude configuration fragments.
- `git diff --check` passed.
- Repository source contains no configured `model`, `advisorModel`, or `env`
  field in `config/claude-settings.json`.
- Exact-key search found no active `model =` override in repository-managed
  Claude/Codex prompts, agents, settings, scripts, or tests; installed Codex
  agent definitions also contain no model override.
- Second real install passed without another legacy migration event.

## Human appropriateness

No separate verdict was required; the user explicitly approved inheritance of
their model preferences.

## Deviations

None.

## Unresolved gaps

None for the approved source and installation scope. The change is not
committed or pushed because neither action was authorized.
