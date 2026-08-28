# Restore the explicit model pairing

## Outcome and actors

Restore the Claude model pairing from historical commit `7815e90`, while using
current 5.6 Codex model names and the user's current Codex role choices. Do not
roll back unrelated improvements added since that commit.

## In scope

- Configure Claude main model `sonnet` and advisor model `opus`.
- Configure the Codex documentation researcher as `gpt-5.6-luna`.
- Remove the Codex safety reviewer role.
- Add a Codex article writer using `gpt-5.6-sol`, and route article-writing work
  to that Sol role.
- Use full `gpt-5.6-*` names for every explicit Codex model selection.
- Preserve the later `crossSessionInbound=accept` setting.
- Preserve hook cleanup, Mini SDD, routing, tests, and other unrelated changes
  introduced after `7815e90`.
- Keep the legacy `CLAUDE_CODE_SUBAGENT_MODEL=sonnet` migration so installations
  from the intermediate worker-pin version do not retain two competing paths.
- Reinstall the restored settings into the real Claude and Codex user roots.

## Out of scope

- Resetting the branch or worktree to commit `7815e90`.
- Reverting unrelated commits after `7815e90`.
- Changing unrelated routing or advisor usage policy.
- Commit, push, tag, release, or hosted deployment.

## Scenarios

1. A fresh install writes `model=sonnet` and `advisorModel=opus` while retaining
   `crossSessionInbound=accept`.
2. An upgrade removes the intermediate
   `env.CLAUDE_CODE_SUBAGENT_MODEL=sonnet` pin and installs the explicit
   main/advisor pairing.
3. Installed Codex agents contain the Luna documentation researcher and Sol
   article writer, with no safety reviewer.
4. Article-writing delegation uses the Sol writer.
5. Uninstall removes repository-managed model values only while they still equal
   the installed values; user-edited values survive.

## Confirmed decisions

- Commit `7815e90` is the historical target for the Claude
  Sonnet-main/Opus-advisor pairing only.
- Codex roles are intentionally modernized: Luna researches documentation, Sol
  writes articles, and the safety reviewer is removed.
- Restoration is a forward change on current `main`, not a Git reset.
- Later unrelated improvements remain in place.

## Open questions

None.
