# Inherit user model preferences design

## Chosen approach

Keep `config/claude-settings.json` for the unrelated managed
`crossSessionInbound` setting, but remove its
`env.CLAUDE_CODE_SUBAGENT_MODEL` entry. Before merging current settings
fragments, the installer runs a narrow
upgrade migration against `~/.claude/settings.json`:

- remove `env.CLAUDE_CODE_SUBAGENT_MODEL` only when it equals the former managed
  value `sonnet`;
- retain every other `env` entry;
- remove `env` itself only when the migration leaves it empty;
- leave user-owned `model`, `advisorModel`, and non-Sonnet worker values intact.

This migration must run before the current fragments are merged. It is an
upgrade cleanup, not a new managed model policy.

## Interfaces and data flow

`scripts/install.sh` remains the public interface:

1. Read an existing Claude settings document if present.
2. Apply the value-sensitive legacy worker-pin migration.
3. Merge the current hooks and non-model settings fragments.
4. Write the resulting settings document through the existing installer path.

`scripts/uninstall.sh` continues to remove only values present in the current
settings fragment. Because model selections are absent from that fragment,
uninstall leaves all user model choices untouched.

Codex agent definitions retain their role-specific instructions, sandbox mode,
and reasoning effort, but omit the `model` key. Their installed symlinks
therefore let Codex inherit the user's active model selection.

## Existing precedent

- `scripts/uninstall.sh` already uses value-sensitive cleanup for managed scalar
  settings.
- `tests/install.sh` and `tests/uninstall.sh` exercise the public scripts against
  isolated fake homes and inspect the resulting settings document.
- The installer already migrates obsolete hook registrations before reporting
  success; the worker-pin cleanup follows the same upgrade principle.

## Decisions and trade-offs

- The legacy value is intentionally explicit in the migration. Removing every
  worker-model value would violate user ownership.
- A user who independently chose exactly `sonnet` through this old environment
  key is indistinguishable from the former managed value. The approved migration
  favors removing the known repository-installed state so dispatch inherits the
  active user preference.
- Historical eval records remain immutable evidence and are not policy inputs.

## Risks

- A shallow removal could delete unrelated environment preferences; tests cover
  a mixed `env` object.
- Merely removing the config key would strand the old pin in installed settings;
  the upgrade test covers an existing installation.
- Installing locally could overwrite user preferences; the real-user-root check
  records the target model/advisor values before and after installation and
  verifies only the legacy worker pin changes.

## Correctness method

The red-capable seam is `bash tests/install.sh` operating on fake homes. Focused
test cases cover fresh installation, legacy migration, and preservation of a
user-selected worker model plus main/advisor/unrelated environment values. The
fresh-install case also parses the installed Codex agent TOML and rejects an
explicit `model` key. The affected `tests/uninstall.sh` suite then proves
uninstall preservation. Shell syntax checks, JSON/TOML parsing, static policy
searches, and a real `bash scripts/install.sh` run provide broader and
installed-state evidence.

## Human appropriateness

No human suitability decision remains; the user explicitly selected inheritance
of their preferences.
