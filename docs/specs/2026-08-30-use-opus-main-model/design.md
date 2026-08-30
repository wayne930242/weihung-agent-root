# Use Opus as the Claude main model design

## Chosen approach

- Change `config/claude-settings.json` from `model=sonnet` plus
  `advisorModel=opus` to `model=opus` with no `advisorModel` key.
- Extend the installer migration step to remove `advisorModel` only when its
  current value is the formerly repository-managed `opus` value.
- Keep a non-Opus advisor value as user-owned state.
- Leave the existing value-sensitive legacy worker-pin migration unchanged.
- Update installer expectations, current documentation, and installer help to
  describe Opus main with no repository-managed advisor.

## Interfaces and data flow

`scripts/install.sh` remains the public interface. Before merging the current
settings fragment, it migrates the former worker pin and former Opus advisor,
then writes `model=opus` and `crossSessionInbound=accept`.

`scripts/uninstall.sh` continues to remove keys present in the current settings
fragment only when their installed values still match. Because `advisorModel`
is no longer in that fragment, uninstall preserves advisor state; the installer
migration is responsible for removing the former managed Opus value.

## Existing precedent

- `migrate_legacy_worker_model_pin` already performs a value-sensitive settings
  migration before fragment merge.
- `clean_managed_settings` already removes current managed keys only on exact
  value match.
- `tests/install.sh` exercises fresh and upgrade behavior through isolated fake
  homes.

## Decisions and trade-offs

- Reuse one migration pass for retired settings so upgrade behavior is explicit
  and idempotent.
- Treat `advisorModel=opus` as former repository state and every other advisor
  value as user-owned. A user who independently selected Opus cannot be
  distinguished from repository-managed state; removing that exact value is the
  necessary migration trade-off.
- Historical specs remain unchanged because they document earlier approved
  behavior.

## Risks

- A purely additive fragment merge cannot delete the old advisor key; focused
  upgrade coverage must observe its removal.
- Broad advisor cleanup could erase a user selection; a non-Opus preservation
  case guards the value-sensitive boundary.
- Updating only the source fragment would leave the real user root stale;
  verification includes the real installer and installed-state inspection.

## Correctness method

First change focused assertions and add upgrade/preservation cases in
`tests/install.sh`, then run them against the current production files to prove
the expected red failures. Implement the migration and settings change, rerun
focused cases, then run full install/uninstall suites, shell syntax checks, JSON
parsing, static text checks, `git diff --check`, the real installer, and
installed-state inspection.

## Human appropriateness

No separate question remains; the user explicitly approved Opus main with the
advisor removed.
