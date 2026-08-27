# Mini Spec 3R verification

Verified: 2026-08-27

## Requirement-to-evidence mapping

| Requirement | Evidence | Result |
|---|---|---|
| Route: a source change declares Inline or Durable before the first production edit | Behavior eval, inline case: the agent opened with `Inline — Contract: …` before its first `Edit`; durable case: it created `docs/specs/2026-08-27-greet-format-option/` before specifying | pass |
| Route: clear, localized, low-reuse work stays inline and writes no artifact file | Behavior eval, inline case: `src/greet.sh` and `tests/greet.sh` were edited and no `docs/specs/` path was created | pass |
| Route: a lasting public contract, stated reuse, or a user asking for the spec first forces durable | Behavior eval, durable case: those three triggers in the prompt produced a durable folder and left `src/` untouched | pass |
| Route: material ambiguity, cross-module or cross-session scope, high risk, and scope expansion also force durable | Written in `SKILL.md` Ground and guarded by `tests/prompts.sh mini_spec_route_declares_inline_or_durable`; no eval case exercises these four triggers individually | unknown |
| Ratify: inline states one observable `Contract:` and records the request as `Authorization:`, then executes | Behavior eval, inline case: both lines present in the turn stream, followed by two `Edit` calls and a passing `tests/greet.sh` run, with no approval question | pass |
| Ratify: `spec.md` opens with `Status`, `Approved at`, and `Approved from` | Behavior eval, durable case: all three fields present in the generated `spec.md` | pass |
| Ratify: `Status: proposed` forbids production-source editing | Behavior eval, durable case: `git diff` on `src/greet.sh` was empty while the spec sat at `proposed` | pass |
| Ratify: only an explicit user reply moves `Status` to `approved`, recording the date and the reply | Behavior eval, durable case: `proposed` and no `approved` before the reply; approved case: `Status: approved`, an ISO date in `Approved at`, and non-empty `Approved from` after resuming the same session with an approval message | pass |
| Ratify: the agent never advances the status on its own judgment | Behavior eval, durable case asserts the absence of `Status: approved` at proposal time | pass |
| Result: `verification.md` carries one `Requirement \| Evidence \| Result` row per requirement | Behavior eval, approved case: 7 individually-judged rows in the generated `verification.md` | pass |
| Result: every verdict is `pass`, `fail`, or `unknown`, and evidence names the interface exercised | Behavior eval, approved case: every table row ends in one of the three verdicts, and no row carries anything else | pass |
| Result: an unexercised requirement stays `unknown` rather than borrowing a green suite | This table: four requirements are recorded `unknown` because nothing exercised them, despite every automated suite passing | pass |
| Result: local verification, commit, push, CI, deployment, and browser proof stay distinct | The Delivery evidence section below records each separately | pass |
| Enforcement: no hook gates, approves, blocks, or advances any part of the contract | `tests/prompts.sh mini_spec_is_not_enforced_by_hooks` scans both hook configs and all four hook scripts and finds no contract vocabulary; the guard was confirmed to fail when a reference was planted | pass |
| Verification: a real agent-behavior eval drives a headless agent against the installed instructions in an isolated home | `evals/mini-spec-3r.sh` installs the repo under `mktemp -d`, copies credentials, and runs `claude -p` with `CLAUDE_CONFIG_DIR` and an empty MCP set; sandboxes retained under `/tmp/mini-spec-3r-qXx0ln` | pass |
| Verification: the eval covers inline execution, durable stop-before-edit, and approved per-requirement evidence | Final run, model `sonnet`: 18 of 18 assertions passed across the three cases | pass |
| Verification: the eval asserts observable outcomes, not narration | Every assertion but the three inline declaration checks reads the sandbox filesystem or `git diff`; the declaration checks read the turn stream because the contract requires those words to be stated | pass |
| Verification: text assertions remain deletion guards only | `tests/prompts.sh` opens with that statement and points at the eval; its Mini Spec functions assert presence and line budget only | pass |
| Standards: the always-loaded root prompt does not grow | `git diff --stat -- CLAUDE.md AGENTS.md shared/` is empty | pass |
| Standards: the Mini Spec surface stays inside its budget | `SKILL.md` 99, `MINI-SDD.md` 47, `DEBUGGING.md` 35, total 181, against 100/50/35/185 | pass |
| Non-goal: no fourth artifact file, task engine, status tracker, or diary | `MINI-SDD.md` still defines exactly four files; `tests/prompts.sh mini_spec_keeps_its_load_bearing_rules` still asserts `no \`tasks.md\`` | pass |
| Non-goal: the Straw Boss dispatch boundary is unchanged | No file under `skills/` other than `leveraging-tasks` changed, and `CLAUDE.md`'s delegation section is untouched | pass |
| No active OpenSpec route | `tests/prompts.sh active_instructions_carry_no_openspec_route` passes over every tracked file outside `docs/` | pass |

## Red-before-green evidence

The eval discriminates. Against the pre-change text, run `/tmp/mini-spec-3r-LSGDpU`
failed all three inline declaration assertions while the edit itself succeeded,
and run `/tmp/mini-spec-3r-YIAKNS` failed on no `spec.md` being created. Both
went green only after the corresponding contract text landed.

Two failures during development were contract defects the eval caught, not
harness noise:

- The inline declaration lost to the root prompt's "no preamble" rule. Fixed by
  making the two lines required output that no brevity rule removes.
- A durable spec was presented in the reply and never written to `spec.md`, so
  no `Status: proposed` record existed. Fixed by requiring the file to be
  written before it is presented.

One failure was a harness defect: the first version read only the final
assistant message, which misses declaration lines stated before work begins. The
eval now reads the whole turn stream.

## Automated results

- `tests/prompts.sh`: pass, including the five new Mini Spec guards.
- `tests/install.sh`, `tests/uninstall.sh`, `tests/hooks.sh`,
  `tests/codex_hooks.sh`, `tests/bootstrap.sh`,
  `tests/install_codex_desktop_wsl.sh`: pass.
- `evals/mini-spec-3r.sh`: 18 of 18 assertions passed on model `sonnet`.
- Guard discrimination checked by planting a hook reference and by renaming an
  eval case; both guards failed as intended and were restored.

## Delivery evidence

- Local verification: complete.
- Behavior eval: complete on `sonnet`; not run on other models.
- Commit: recorded below once made.
- Push: recorded below once made.
- Install probe: recorded below once run.
- CI: none configured.
- Deployment: not applicable.
- Browser proof: not applicable.
