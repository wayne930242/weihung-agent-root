# Restore explicit model pairing design

## Chosen approach

Restore the Claude pairing as a current settings fragment rather than resetting
Git history:

- `config/claude-settings.json` manages `model=sonnet`, `advisorModel=opus`, and
  the existing `crossSessionInbound=accept` value.
- The existing installer migration continues to remove the intermediate
  `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` environment pin before merging current
  settings.
- `docs-researcher.toml` gains `model=gpt-5.6-luna` while retaining its current
  reasoning effort, sandbox, and instructions.
- `safety-reviewer.toml` is retired and replaced by a distinct
  `article-writer.toml` using `model=gpt-5.6-sol`. The writer has workspace-write
  access, writes only user-requested article content, and has no publish/commit
  authority.
- Claude direct consultation routes article writing to `gpt-5.6-sol`; the old
  deep/adversarial review route is removed from this Codex responsibility.

## Interfaces and data flow

`scripts/install.sh` remains the public installation interface. It:

1. Removes only the retired safety-reviewer symlink whose target is this
   repository's former agent path.
2. Links the current Luna researcher and Sol article writer.
3. Removes the intermediate Claude worker pin when present.
4. Merges the restored Claude model/advisor/cross-session fragment.

`scripts/uninstall.sh` performs the same target-sensitive cleanup for an older
safety-reviewer symlink, then removes current managed links and value-matching
Claude settings through existing behavior.

## Existing precedent

- Commit `7815e90` provides the Claude Sonnet/Opus configuration precedent.
- The current installer already performs value-sensitive migration for the
  intermediate Claude worker pin.
- Installer link handling compares exact symlink targets before treating an
  existing path as repository-managed.
- Codex agent definitions already separate model, effort, sandbox, and role
  instructions.

## Decisions and trade-offs

- Codex roles use current full model IDs rather than historical 5.4 names.
- The article writer is a new role instead of renaming the safety reviewer, so
  role intent and authority remain explicit.
- Retired-link removal is exact-target only. A regular file or symlink with the
  same name but a different target is user-owned and survives.
- The Sol writer receives workspace-write because producing repository article
  content requires writes; publishing, committing, and pushing remain outside
  its authority.

## Risks

- Additive installation would otherwise strand a broken safety-reviewer link;
  focused upgrade tests cover exact-target cleanup.
- Broad stale-link cleanup could delete user-owned agents; preservation tests
  cover a different-target link.
- Restoring main/advisor settings could overwrite a current user choice. This is
  intentional repository-managed behavior approved by the user; uninstall
  remains value-sensitive so later user edits survive.

## Correctness method

Use `tests/install.sh` and `tests/uninstall.sh` through their public fake-home
interfaces. Red/green slices cover the Claude pairing, Luna/Sol installed agent
definitions, article-routing text, exact-target retirement, user-owned same-name
preservation, legacy worker migration, and user-edited uninstall preservation.
Then run complete suites, syntax/JSON/static checks, the real installer, and
installed-state inspection.

## Human appropriateness

No separate suitability question remains; the user explicitly confirmed the
Claude pairing, Luna researcher, Sol writer, and removal of the safety reviewer.
