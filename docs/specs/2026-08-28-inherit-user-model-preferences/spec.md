Status: approved
Approved at: 2026-08-28T12:23:16+08:00
Approved from: 使用者回覆「核准」

# Inherit user model preferences specification

## Observable behavior

1. A fresh installation does not write `model`, `advisorModel`, or
   `env.CLAUDE_CODE_SUBAGENT_MODEL` into `~/.claude/settings.json`.
2. Installing over the former repository-managed state removes
   `env.CLAUDE_CODE_SUBAGENT_MODEL` only when its value is the former managed
   value `sonnet`. If that removal leaves `env` empty, the empty object is also
   removed.
3. Installation preserves user-owned `model`, `advisorModel`, a worker-model
   value other than the former managed `sonnet`, and unrelated `env` entries.
4. Current repository documentation states that main, advisor, and worker model
   selection all inherit user preferences; it no longer recommends or pins the
   Sonnet-main/Opus-advisor or Sonnet-worker combinations.
5. Installing into the real user root removes the former managed worker pin
   while preserving the current user-owned advisor preference.

## Edge cases

- Missing `~/.claude/settings.json` remains valid.
- A missing or non-object `env` value must not make installation fail.
- An `env` object containing both the former pin and unrelated values loses only
  the former pin.
- A user-selected worker value other than `sonnet` survives install and
  uninstall.

## Compatibility constraints

- Existing Claude/Codex prompt links, hooks, agents, skills, rules, and status
  line installation behavior remain unchanged.
- Existing user settings not named by this specification remain unchanged.
- The migration is intentionally value-sensitive because the former installer
  wrote `sonnet`; no other worker-model value is treated as repository-owned.

## Non-goals

- The repository does not infer which model the user prefers.
- The repository does not enable, disable, or select an advisor.
- Eval harness defaults and historical verification records are not dispatch
  policy and are not changed by this work.
- No commit, push, release, or hosted deployment is authorized.

## Applied standards

- [`AGENTS.md`](../../../AGENTS.md): read before write, minimum requested scope,
  relevant verification, and no unrelated cleanup.
- [`skills/leveraging-tasks/SKILL.md`](../../../skills/leveraging-tasks/SKILL.md):
  durable lifecycle and per-requirement verification evidence.
- [`skills/tdd/SKILL.md`](../../../skills/tdd/SKILL.md): installer behavior changes
  proceed through a failing test before production changes.

## Evidence and precedent

- [`config/claude-settings.json`](../../../config/claude-settings.json) currently
  installs the former worker pin.
- [`scripts/install.sh`](../../../scripts/install.sh) currently deep-merges that
  fragment, so deleting the source key alone would leave the installed pin
  behind.
- [`tests/install.sh`](../../../tests/install.sh) currently asserts the Sonnet
  worker pin, and provides the executable seam for fresh-install and migration
  behavior.
- [`README.md`](../../../README.md) already treats main/advisor selection as a
  personal preference but retains a worker-model exception that this change
  removes.

## Correctness strategy

The agent-owned interface is the installer test harness operating against
isolated fake homes, followed by `bash scripts/install.sh` against the real user
root. Tests must prove fresh install, legacy-pin migration, preservation of a
user-changed worker model, and preservation of main/advisor/unrelated env
settings. Static checks must prove current policy text and source configuration
contain no active Sonnet/Opus dispatch recommendation or model pin.

## Human appropriateness question

None. The requested preference boundary is explicit.
