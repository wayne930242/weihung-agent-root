# Restore explicit model pairing verification

## Requirement evidence

| Requirement | Evidence | Result |
|---|---|---|
| Repository Claude settings contain Sonnet main, Opus advisor, cross-session accept, and no worker pin | JSON parse and direct source inspection of `config/claude-settings.json` | pass |
| Fresh install writes the explicit Claude pairing without a worker override | Full `bash tests/install.sh`; `fresh_install_manages_explicit_model_settings` inspected fake-home settings | pass |
| Upgrade removes the intermediate worker pin before installing the pairing | `legacy_worker_pin_is_replaced_by_explicit_pairing` and mixed/empty `env` cases | pass |
| Installed documentation researcher selects `gpt-5.6-luna` | Fresh-install agent inspection plus real installed-agent inspection | pass |
| Installed article writer selects `gpt-5.6-sol` and article work routes to Sol | Fresh-install agent/prompt checks plus real installed-agent and `CLAUDE.md` inspection | pass |
| Repository and installed Codex roots contain no safety reviewer | Source absence check; exact-target install/uninstall retirement tests; real install removed the old symlink | pass |
| Every active explicit Codex model name uses the GPT-5.6 family | Static search over active prompts, agents, config, scripts, and tests found no GPT-5.4 selection | pass |
| Current documentation describes the explicit pairing and current Codex roles | Agent diff review of `README.md` and installer help | pass |
| Real user-root model state matches repository source | `bash scripts/install.sh`; installed settings reported Sonnet/Opus, Luna researcher, Sol writer, and no safety reviewer | pass |
| Unrelated environment values and user-selected nonlegacy worker values survive installation | Full install suite mixed-env, custom-worker, and non-object-env cases | pass |
| User-edited main/advisor values survive uninstall | Full `bash tests/uninstall.sh`; `uninstall_keeps_user_model_preferences` | pass |
| User-owned same-name safety-reviewer links survive install and uninstall | Focused exact-target preservation cases in both public script suites | pass |

## TDD evidence

- Red: fresh agent installation failed because `article-writer.toml` did not
  exist; fresh settings failed because `model` was absent; retirement failed
  because the old managed safety link remained; user-owned link preservation
  failed because the old role still claimed that path.
- Green: focused Claude pairing, Luna/Sol agent, routing, retirement, migration,
  and preservation cases all passed after the implementation.
- Regression: complete install and uninstall suites both exited 0.

## Additional validation

- Shell syntax checks passed for installer, uninstaller, and both test scripts.
- Both Claude JSON fragments parsed successfully.
- `git diff --check` passed before real installation.
- Real installation completed without `--force` and preserved all unrelated
  managed links.

## Human appropriateness

The user confirmed the corrected 5.6 role mapping with「正確」.

## Deviations

None.

## Unresolved gaps

None for the approved source and installation scope.
