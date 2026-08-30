Status: approved
Approved at: 2026-08-30T12:14:13+08:00
Approved from: 使用者回覆「確認」

# Use Opus as the Claude main model specification

## Observable behavior

1. `config/claude-settings.json` contains `model: opus` and
   `crossSessionInbound: accept`, with no `advisorModel` or persistent
   `CLAUDE_CODE_SUBAGENT_MODEL` entry.
2. A fresh real or fake-home install writes the Opus main and cross-session
   settings without advisor or worker-model overrides.
3. An upgrade from the former repository-managed Sonnet main setting installs
   Opus as the main model and removes the former managed Opus advisor setting.
4. Current documentation describes Opus main with no repository-managed
   advisor.
5. The real user-root installation has the same named model values as the
   repository source after reinstall.

## Edge cases

- The legacy `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` migration remains
  value-sensitive and preserves unrelated environment values.
- A user-selected worker-model value other than the legacy managed Sonnet value
  survives installation.
- Install removes only the former managed `advisorModel=opus` value; a
  user-selected non-Opus advisor value survives.
- Uninstall removes `model` only while it still holds the repository-managed
  `opus` value and preserves any user-selected advisor value.

## Compatibility constraints

- Preserve `crossSessionInbound=accept`, hook/status-line merge behavior, and
  existing Codex role models.
- Preserve the legacy worker-pin migration without introducing a replacement
  worker pin.
- Preserve historical specification records as evidence of earlier behavior.

## Non-goals

- No Codex model or routing change.
- No persistent Claude worker-model selection.
- No commit, push, tag, release, or hosted deployment.

## Applied standards

- [`AGENTS.md`](../../../AGENTS.md): read before write, scoped changes, relevant
  verification, and no unrelated cleanup.
- [`skills/leveraging-tasks/SKILL.md`](../../../skills/leveraging-tasks/SKILL.md):
  durable lifecycle and per-requirement verification evidence.
- [`skills/tdd/SKILL.md`](../../../skills/tdd/SKILL.md): public installer tests
  go red before production setting changes.

## Evidence and precedent

- [`config/claude-settings.json`](../../../config/claude-settings.json) currently
  manages Sonnet main and Opus advisor.
- [`tests/install.sh`](../../../tests/install.sh) is the executable public seam
  for fresh install, upgrade, legacy worker migration, and preservation behavior.
- [`tests/uninstall.sh`](../../../tests/uninstall.sh) is the executable public
  seam for value-sensitive cleanup and user preference preservation.

## Correctness strategy

Update the focused public installer and uninstaller expectations first and run
them red against the current Sonnet configuration. Then change the settings and
uninstall cleanup, update current documentation, and run both full suites,
shell/JSON checks, `git diff --check`, and the real installer. Finally inspect
only the named installed model fields and managed links.

## Human appropriateness question

None after the user confirms Opus main with no repository-managed advisor.
