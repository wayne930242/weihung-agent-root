Status: approved
Approved at: 2026-08-28T13:06:09+08:00
Approved from: 使用者回覆「正確」

# Restore explicit model pairing specification

## Observable behavior

1. `config/claude-settings.json` contains `model: sonnet`,
   `advisorModel: opus`, and `crossSessionInbound: accept`, with no persistent
   `CLAUDE_CODE_SUBAGENT_MODEL` entry.
2. A fresh real or fake-home install writes the Claude main/advisor pairing and
   cross-session setting without a worker-model environment override.
3. An upgrade from the intermediate worker-pin configuration removes the legacy
   worker pin before installing the main/advisor pairing.
4. Installed `docs-researcher.toml` selects `gpt-5.6-luna`.
5. Installed `article-writer.toml` selects `gpt-5.6-sol`, and article-writing
   delegation routes to that Sol role.
6. The repository and installed Codex agent roots contain no safety reviewer;
   an older repository-managed safety-reviewer symlink is removed on upgrade.
7. Every explicit Codex model selection uses a full `gpt-5.6-*` model name.
8. Current documentation describes the restored explicit pairing rather than
   inheritance-only behavior.
9. The real user-root installation has the same model values as repository
   source after reinstall.

## Edge cases

- Unrelated Claude `env` values survive legacy worker-pin migration.
- A user-edited worker-model environment value other than the legacy managed
  `sonnet` value survives installation.
- Uninstall removes the repository-managed main/advisor values only when they
  still equal `sonnet`/`opus`; a user-edited value survives.
- Removing the old safety reviewer does not remove unrelated user-owned Codex
  agents.

## Compatibility constraints

- Preserve `crossSessionInbound=accept` and all current hook/status-line merge
  behavior.
- Preserve the documentation researcher's current reasoning effort, sandbox
  mode, and developer instructions while updating only its model.
- The article writer is a writing role, not a renamed safety reviewer; its
  instructions focus on producing user-requested articles.
- Preserve every post-`7815e90` change outside the explicit model-setting
  surface.

## Non-goals

- Do not reset current `main` to `7815e90`.
- Do not restore obsolete README benchmark claims unless needed to describe the
  active pairing accurately.
- Do not restore the historical GPT-5.4 Codex model selections.
- Do not add a separate Claude worker-model pin.
- No commit, push, tag, release, or hosted deployment is authorized.

## Applied standards

- [`AGENTS.md`](../../../AGENTS.md): read before write, scoped changes, relevant
  verification, and no unrelated cleanup.
- [`skills/leveraging-tasks/SKILL.md`](../../../skills/leveraging-tasks/SKILL.md):
  durable lifecycle and per-requirement verification evidence.
- [`skills/tdd/SKILL.md`](../../../skills/tdd/SKILL.md): public installer tests
  go red before model-setting production changes.

## Evidence and precedent

- Commit `7815e90` contains the requested Claude `model=sonnet` and
  `advisorModel=opus` pairing; its Codex 5.4 roles are explicitly not the target.
- Commit `c61a2d6` removed main/advisor selection and introduced the intermediate
  Claude worker-model pin.
- Commit `3218eac` removed the remaining persistent pins while preserving a
  migration for the intermediate worker-model state.
- The current supported Codex model family exposed to this workspace includes
  `gpt-5.6-luna` and `gpt-5.6-sol`; the user selected Luna for documentation
  research and Sol for article writing.
- Current installer and uninstall tests are the executable public seam for
  settings merge, migration, preservation, and cleanup behavior.

## Correctness strategy

Use `bash tests/install.sh` and `bash tests/uninstall.sh` against isolated fake
homes. Focused red/green cases must prove the restored Claude pairing, legacy
worker-pin migration, Luna researcher, Sol writer, removal of the old managed
safety-reviewer link, article-writing routing, and value-sensitive uninstall.
Then run both full suites, shell/JSON checks, `git diff --check`, and
`bash scripts/install.sh` against the real user root. Inspect only the named
installed model fields, roles, routing text, and managed links.

## Human appropriateness question

None after the user confirms the corrected Claude pairing and 5.6 Codex roles.
