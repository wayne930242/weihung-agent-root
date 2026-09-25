# Pi harness migration verification

## Integrated Pi instruction rewrite (2026-09-25)

Baseline: the pre-change real-HOME `~/.pi/agent/AGENTS.md` (1,234 words). The table maps every directive in that generated file; repeated shared rules are listed together by their baseline line numbers.

| Baseline rule | New location or disposition |
|---|---|
| Traditional Chinese communication (line 1) | Retained positively in Language and communication. |
| English prompts and agent instructions (line 3) | Retained in Language and communication. |
| Direct expected behavior and concise replies (lines 5–6) | Retained in Language and communication. |
| Source changes use `aaaav-do` and state Alignment and Reality anchor (lines 7, 14, 28) | Retained in Work and Verification and delivery; duplicate wording is consolidated. |
| Resolve uncertainty from conversation before asking (line 8) | Retained as resolving assigned execution choices and bringing user-owned decisions with context and a recommendation. |
| Choose the specialized skill or research/review/explanation/feedback/decision skill (line 12) | Retained in Work. |
| Read model profile before choosing a delegated model and respect user choice (line 16) | Retained in Model and dispatch. |
| Use active tier model and thinking and provide worker objective, cwd, ownership, anchor, model, thinking, and app guide (lines 16, 20) | Retained in Model and dispatch; the full ordered model list is explicit. |
| Workers have assigned permission; worktree persists for review; main integrates (line 20) | Retained as execution within assigned scope and main-session review/integration. |
| Carry bounded work; use visible cross-app/check-out Pi worker when useful (line 20) | Retained in Model and dispatch. |
| Outside Herdr explain pane dispatch is unavailable and continue in the current session (line 22) | Retained in Model and dispatch. |
| Recover workers, contact related main sessions, and hand off a scope (line 22) | Retained through `dispatch-recovery`, `intercom`, and `orchestrator-handoff`. |
| Use app's Git workflow for branch/worktree, commit, PR, merge (line 22) | Retained through `shipping-task`. |
| Ask users about consequential decisions with context and recommendation (line 24) | Retained in Model and dispatch; combined questions are covered by the concise recommendation rule. |
| Track multi-step work and report actual worker result (line 24) | Retained through `todo` and explicit result reporting. |
| Explain reasoning, report problems, read first, make scoped changes, verify, use the required languages, and avoid AI attribution in commits (line 28) | Retained in Language and communication, Work, Verification and delivery; duplicate rules are consolidated. |
| Read app guide, check project skills, and follow applicable language/Git/deployment/UI rules (line 30) | Retained in Work. |
| Translate Windows attachment paths in WSL and quote the translated path (line 32) | Retained in Work. |
| Use graph tools for symbols, calls, snippets, and architecture (line 36) | Retained in the single Code discovery section. |
| Query existing graph first; index missing project once; re-index when stale (line 36) | Retained in Code discovery. |
| Check coverage, read uncovered lines, and text-search prose/config/scripts/literals (line 36) | Retained in Code discovery. |
| Explain decisions, surface problems, speak directly, and reassess repeated failures (lines 42–45) | Retained across Language and communication, Work, and Verification and delivery. |
| State assumptions, surface tradeoffs, resolve ambiguity, and do not hide confusion (lines 49–56) | Retained as explaining assumptions/tradeoffs and distinguishing execution choices from user-owned decisions; rhetorical repetitions are consolidated. |
| Give exact TTL when discussing cache expiry (lines 60–61) | Dropped: this narrow cache-reporting case is outside the core Pi work instructions and can be verified from the relevant source when it applies. |
| Follow the user's architecture and suggest refactoring for poor architecture (lines 64–66) | Following the user's architecture is retained. The unsolicited-refactor directive is dropped; report material problems and keep changes within the requested scope. |
| Read files and understand existing patterns before edits (line 67) | Retained as Read before editing. |
| Avoid unrequested docs, refactors, and adjacent changes (line 68) | Retained as scope control and cleanup of only changes made by this work. |
| Avoid extra features, single-use abstractions, unrequested configurability, impossible-case handling, and overlong solutions (lines 74–80) | Retained in the smallest useful approach; illustrative examples are omitted. |
| Avoid adjacent formatting/refactors; match style; report rather than remove unrelated dead code; clean only new orphans (lines 86–94) | Scope and owned-cleanup rules are retained. Existing project style and user request govern formatting; old cleanup examples are omitted. |
| Prefer composition, explicit dependencies, single-purpose functions, domain organization, and no hypothetical design (lines 100–102) | Dropped as generic design advice; follow the target app's established architecture and the user's chosen approach instead. |
| Translate requests into measurable outcomes and use examples (lines 104–118) | Verifiable goal, Reality anchor, and behavior checks are retained; examples are omitted. |
| Deliver finished code without TODOs, stubs, or mocks (line 123) | No TODOs or stubs are retained. Mock policy is left to the relevant test or project rules. |
| Test before deployment and verify destructive deploy commands (line 124) | Testing before deployment is retained; deployment-specific safeguards come from the app's deployment rules. |
| Keep commit messages free of AI tool attribution (lines 28, 125) | Retained once in Verification and delivery. |
| Summarize/checkpoint after research, difficult debugging, and failed attempts; preserve context through verification (lines 128–131) | Retained in Work. |
| Active strategy, tier model lists, thinking levels, and dispatch model-selection guidance, including supported `task:` categories (lines 133–146) | Retained dynamically in the Active model strategy section generated from the current profile. |

| Requirement | Evidence | Result |
|---|---|---|
| Pi instructions come from one integrated template without appended Claude/shared content | `python3 tests/pi_port_install.py` asserts generated output has no `@shared/` imports or legacy `boss-say`/`/codex:rescue` references. | pass |
| Generated instructions stay within 500–700 words | `python3 tests/pi_port_install.py` passed; after final template edits, `scripts/pi-target.py` measured 657 words. | pass |
| Exactly one code-discovery section and one AI-attribution commit rule remain | `python3 tests/pi_port_install.py` asserted one of each; the real-HOME file has one `## Code discovery` heading and one commit attribution rule. | pass |
| Real HOME file is regenerated within range and Pi loads it | `bash scripts/install.sh --target pi` exited 0. `~/.pi/agent/AGENTS.md` measured 657 words. Pi RPC returned a successful `get_state` response with the configured model and eight MCP servers. Both `openai-codex/gpt-6-luna` and `claude-bridge/claude-opus-5-5` answered a prompt about the loaded language and commit rules correctly; neither startup reported errors. | pass |

The unrelated `tests/bootstrap.sh` run was stopped after its external codebase-memory binary and Chrome downloads remained below 15% after several minutes. The direct install, uninstall, prompt, Pi target, Pi runtime, profile, and Python suites ran independently; this bootstrap result is not evidence about the Pi instruction generator.

## Claude plugin ports (2026-09-25)

| Requirement | Evidence | Result |
|---|---|---|
| Official codebase-memory Pi integration without a second instructions block | The target ran `codebase-memory-mcp install --clients=pi -y` in a staging HOME, installed its generated `cbmem.ts` and skill in the real HOME, and replaced the staged binary path with `~/.local/bin/codebase-memory-mcp`. The generated Pi `AGENTS.md` has one `Code discovery` section. Pi RPC loaded with zero extension errors and listed `skill:codebase-memory`. | pass |
| mp-infra skills and hooks in Pi | The live marketplace checkout supplies all 14 current skills (the scope inventory said 13); Pi RPC listed all 14. `node --experimental-strip-types tests/pi-mp-infra-hooks.mjs` ran the original production hook: `DROP DATABASE example` blocked, `echo hello` passed, and `git reset --hard` required interactive review. The same test observed the original session-start output and appended playbook, Nomad, and decrypted-vault findings to model-facing edit/write results. | pass locally |
| team-toon-tack skill, commands, and CLI | The private-prefix npm package is version 3.10.2. Pi RPC listed `skill:managing-linear-tasks` and all 12 `ttt-*` prompts; `~/.local/bin/ttt version` returned `team-toon-tack v3.10.2`. | pass |
| Repeatable Pi install and Pi uninstall | `python3 tests/pi_port_install.py` first withheld the CLI link and observed an install failure with recorded port resources, then reran `bash scripts/install.sh --target pi` twice and `bash scripts/uninstall.sh --target pi` under a temporary HOME with external commands stubbed. It checked 14 mp-infra links, the official integration artifacts, 12 prompts, CLI, user-file restoration, and retention of `moshi-hooks.ts`. Two consecutive real-HOME installs exited 0 and left the settings, instructions, marker, hook config, cbmem extension, and Herdr config byte identical. The real HOME was not uninstalled. | pass for temporary HOME and real reinstall |
| Default and legacy targets | `bash tests/install.sh` and `bash tests/uninstall.sh` exited 0 after the port. | local test pass |

The first real-HOME install stopped at a wrong npm prefix CLI path after writing new port resources. The adapter now records each resource as it installs, uses `node_modules/.bin/ttt`, and a second real-HOME install completed. `git diff --check` passed.

Reflexive pass: the post-edit validator path was nested under `tool_input` (gap; resolved by the adapter and hook test); npm's local prefix used `node_modules/.bin` (gap; resolved by the installer and interrupted-install test); the Nomad matcher and script supported different suffixes (gap; resolved by the Pi adapter's additional triggers); zsh's `status` variable rejected an exit-code assignment (gap; local command slip resolved with `pi_port_rc`). The solid-loop no-op check found no standing instruction to change.

Status: real HOME Pi target installed after user authorization; the core Herdr paths below were verified. Legacy targets remain installed until the user chooses to remove them.

## Pi interface and idle compaction follow-up (2026-09-25)

| Requirement | Evidence | Result |
|---|---|---|
| Workers open in a right split beside the parent | A real Herdr Pi session launched a `subagent` with `openai-codex/gpt-6-luna`; the result returned to the parent as `package.json`. A second run captured `herdr pane layout --pane wZ:p5M` while its worker was active: two panes in tab `wZ:t1Z`, at x=0 and x=92, with `direction: right`. [Layout capture](/Users/weihung/.straw-boss/plans/pi-migration/artifacts/t3-pi-layout.json). | pass |
| Pi theme, footer, and extension load render in Herdr | The real pane loaded `catppuccin-mocha`, `pi-powerline-footer`, and `idle-compaction.ts` without a startup extension error. The ANSI pane capture shows Catppuccin RGB colors and the Powerline model, path, context, subagent, and MCP segments. [Pane capture](/Users/weihung/.straw-boss/plans/pi-migration/artifacts/t3-pi-ui-pane.ansi.txt). Visual taste remains for the user to judge. | pass for rendering; human verdict pending |
| Compaction requests occur only while idle and above 300,000 tokens | `node --experimental-strip-types tests/pi-idle-compaction.mjs` passed active-turn, exact-threshold, pending-message, above-threshold, in-flight, and unknown-usage checks. A live 300,000-token session was not constructed. | local test pass; live threshold unknown |
| Pi install is repeatable and uninstall restores prior settings | `bash tests/install.sh target_matrix_preserves_each_surface` passed a repeated temporary-HOME install, package and UI assertions, and uninstall restoration. On the real HOME, two consecutive full `bash scripts/install.sh --target pi` runs left `settings.json`, `herdr-agents/config.json`, `AGENTS.md`, and the install marker byte identical. `moshi-hooks.ts` remained present. | pass |
| Default and legacy targets retain their behavior | `bash tests/install.sh`, `bash tests/uninstall.sh`, and `python3 -m unittest tests.pi_review_fixes -q` passed after the target change. | local test pass |

Reflexive: The npm search one-liner error was a tool-use slip (`gap`), resolved by a corrected query. Pi's first reinstall changed package order (`gap`), resolved in `scripts/pi-target.py` and verified with real-HOME hashes. An initial layout file was captured after the worker closed (`gap`); the second live run replaced it with an active-worker capture. The `solid-loop` no-op check found no standing instruction to change.

| Spec | Evidence | Result |
|---|---|---|
| 1. Install targets | `bash tests/install.sh`; the target matrix exercised default, each target, repeated Pi install, `full`, and generated settings under temporary HOME. `bash scripts/install.sh --target pi` exited 0 on the real HOME after the user checkpoint; Pi remains 0.87.1 and its Herdr integration reports current v9. A repeat install changed the bridge to `git:github.com/elidickinson/pi-claude-bridge@227f5eb4450a070dfbc083a7fe75b8b35366b941`, retired the npm bridge declaration, and the checkout HEAD matched the requested commit. A second repeat preserved `settings.json`, `config.json`, `AGENTS.md`, and the install marker byte for byte. | Local and real install pass, including stable repeat run after the git migration. |
| 2. Uninstall targets | `bash tests/uninstall.sh` and target matrix; Pi uninstall retained preexisting packages and restored a preexisting `AGENTS.md` and `herdr-agents` model config. | Local pass; real HOME pending. User owns when old targets are removed. |
| 3. Session resources | Real HOME Pi RPC loaded 45 commands with no stderr, including the user-root and aaaav skills; MCP status showed eight servers enabled. Generated instructions expanded all shared imports and enabled MCP host discovery. A Pi process in Herdr reported idle, and a Herdr Pi turn called codebase-memory MCP `list_projects` before replying `MCP_OK`. OAuth became ready after the user ran `/login`; a Herdr Luna turn replied `PI_CODEX_OK`. After the git pin, a new Herdr Claude bridge turn replied `PINNED_BRIDGE_OK`, and `pi --list-models claude-opus-5-5` displayed a 1M context window. | User instructions, skills, both model families, local MCP, and Herdr status pass. OAuth MCP pending; actual 1M serving on this subscription was not measured. |
| 4. Dispatch | In a real Herdr Pi session, `subagent` with `cwd=/Users/weihung/projects/aaaav`, `model=task:recon`, and `thinking=medium` opened a worker pane. The worker read README.md, used `openai-codex/gpt-6-luna`, made no edits, and its result appeared automatically in the parent. | Cross-repo dispatch, model tier, thinking, visible pane, and automatic delivery pass; fallback and permission behavior pending. |
| 5. Recovery | `node --experimental-strip-types tests/pi-dispatch.mjs` exercised parent restart and sidecar completion. `python3 tests/pi_dispatch_cli.py` exercised roll-call and reattach with mocked Herdr. After a real completed dispatch, parent restart reconciled the persisted `subagent_result` without duplication. A normal Pi exit aborted an active worker; `reattach` resumed its child session in a new pane, delivered `recovered_dispatch_result`, and marked the ledger done. In a separate test, the dedicated parent process was terminated unexpectedly while a worker was sleeping; the worker completed independently, and restarting the parent session delivered its result and marked the ledger done. | Parent restart, worker reattachment, and recovered delivery pass in Herdr. Normal exit aborts active workers, so reattachment is required in that case. |
| 6. Inter-main coordination | `pi-intercom` was included in the isolated package load; the CLI test exercised handoff with mocked Herdr. Two dedicated Herdr Pi sessions in different repositories used `intercom list` and `send`; the receiver displayed `INTERCOM_UAT_PING` and automatically ran a turn. A separate `dispatch_control` handoff created a receiving Pi pane in the caller's workspace, sent its summary, and the receiver called `roll-call`, found no active dispatches, and replied `HANDOFF_UAT_OK`. The 2026-09-25 repair pass also handed off a live worker; its evidence is below. | Real peer discovery, message delivery, empty-scope handoff, and active-dispatch handoff pass. |
| 7. Shipping | The local Pi package exposes `shipping-task` in an isolated load. | Target app branch, commit, PR, CI, and merge workflow pending an approved real task. |
| 8. Model profile | Temporary HOME tests applied the active profile, switched a copied profile to `codex-first`, applied it again, and confirmed the Pi default changed to `openai-codex/gpt-6-sol` while recon mapped to Luna; uninstall restored previous settings. `node tests/profile.mjs` passed. User confirmed Gemini/agy to Codex Luna, then superseded the former 200K choice by pinning the upstream bridge commit with Opus 5.5 1M. The real `task:recon` dispatch selected Luna medium. | Local strategy switching and one live tier pass; real HOME strategy switching, other tiers, and fallback pending. |
| 9. aaaav | The adjacent aaaav package has a Pi manifest and loaded in isolated Pi. In a real Herdr Pi process, the `write` tool created a temporary `SKILL.md`; its `tool_execution_end` content included `[aaaav]` feedback for missing YAML frontmatter. The temporary file and pane were removed. | Real write-hook feedback pass; edit-hook branch follows the same extension handler and was not separately exercised. |

Additional checks: `bash tests/install.sh`, `bash tests/uninstall.sh`, `bash tests/prompts.sh`, `node tests/profile.mjs`, `node --experimental-strip-types tests/pi-dispatch.mjs`, `python3 tests/pi_dispatch_cli.py`, Python syntax compilation, and `git diff --check` all passed after the pin change. The Pi recovery extension RPC load and actual `pi-herdr-agents` extension load against generated temporary-HOME config passed. `pi auth check --provider openai-codex --no-refresh --json` returned `ready` after user login. The pinned git bridge's install reported seven dependency advisories; a later `npm audit --json` reported eight transitive advisories (four high, three moderate, one low). No upstream dependency versions were changed.

The model-preference skill applies local Pi settings when it switches strategies. The separate web console currently updates the strategy entrypoint through its remote repository flow; it does not run the local Pi profile application script. A web-console switch therefore needs a local `apply-profile` run before the next Pi dispatch.

## Review-fix verification (2026-09-25)

Six tests in `tests/pi_review_fixes.py` were run before the repairs and all six failed on their corresponding findings. The active-handoff runtime test in `tests/pi-dispatch.mjs` was also run before its final repair and failed because the transfer handler was absent. After repair, `python3 -m unittest tests.pi_review_fixes -v`, `bash tests/install.sh`, `bash tests/uninstall.sh`, `bash tests/prompts.sh`, `node tests/profile.mjs`, `node --experimental-strip-types tests/pi-dispatch.mjs`, `python3 tests/pi_dispatch_cli.py`, and `git diff --check` all exited 0.

| Requirement | Evidence | Result |
|---|---|---|
| Legacy Claude/Codex routing remains usable | The regression test checks all seven strategy files for selection and application rules, including explicit agent-kind/model/effort rows in the six strategies that previously had them. The managing-model-preferences skill now names both legacy and Pi sources. | Local pass. |
| Plain uninstall retains Pi's shared skills | An isolated HOME received a full install, then plain `uninstall.sh`; the Pi marker and `~/.agents/skills/managing-model-preferences` link remained. | Local pass. Real HOME legacy targets were not removed. |
| An active handoff has one result owner | The CLI test observed `transferred` in the old ledger before receiver startup and covered a transient `agent_pane_busy` retry. In real Herdr, the receiving Pi session imported a running worker, then its ledger reached `done` with `delivered=true`. The old Pi session persisted one `transferred_dispatch_notice` and zero `subagent_result` messages; the receiver persisted one `recovered_dispatch_result`. The test tabs were closed. | Real Herdr model-context delivery pass. The upstream widget in the old pane still displayed worker completion. |
| Every Pi tier has model and fallback selection | The regression test checked the six supported `pi-herdr-agents` task categories plus explicit ordered model lists and thinking levels for every profile tier; the default list has no duplicate. The real Pi session loaded `pi-herdr-agents` with the generated config and started a `task:recon` Luna worker. | Local config and real package-load pass; live fallback after provider failure remains untested. |
| A previous git bridge revision is restored | An isolated HOME started with another bridge git commit; Pi install left only the pinned commit, and Pi uninstall restored the original package list. A second red-before-green test emulated an external Pi installer retaining both registrations; the repair removed the old source without calling Pi's repository-wide git removal. | Local pass. |
| A failed external install can retry or uninstall | A stub npm command failed on the first external step. The marker remained with `integration_installed=false`; Pi uninstall removed it. A second failure followed by retry succeeded without `--force`, then uninstall succeeded. | Local pass. |

The real HOME `bash scripts/install.sh --target pi` completed after the repair; `settings.json` contains one pinned bridge package, `herdr-agents/config.json` contains the six accepted task categories, and the install marker records integration state. No legacy target was uninstalled from the real HOME.

### Reflexive pass for the repair

- Friction: the full installer reached unrelated codebase-memory setup before the injected npm failure (gap). Action: resolved by testing `pi-target.py` directly.
- Friction: `pi-herdr-agents` accepts six task categories and rejected the first generated config (gap). Action: resolved by six configured task lists, explicit lists for the other tiers, and a real extension-load check.
- Friction: Herdr reported `agent_pane_busy` after a new pane showed a shell (gap). Action: resolved by a bounded retry for that state.
- Friction: a shortened patch context missed the existing design sentence (gap). Action: resolved by reading and matching the complete paragraph; no standing instruction needed.
- Friction: the old `pi-herdr-agents` watcher sent its own result after ledger transfer (gap). Action: resolved by replacing that old model message with a transfer notice and forwarding the result to the receiving main session.
- Friction: Pi's git removal matches repository identity and would remove a newly installed commit (gap). Action: resolved by exact-source settings cleanup, with an external-install stub test.

The `solid-loop` pass found no standing agent instruction to change: each interface fact now lives in the design and executable checks, and the patch-context slip was local to this edit.

## Handoff completion race follow-up (2026-09-25)

`node --experimental-strip-types tests/pi-handoff-race.mjs` ran against commit `2e7fa92` before the fix and failed with two deliveries for a worker completing while `tab create` was in progress. After the fix it passed: a successful transfer delivered once to the receiver, and a failed pane creation restored delivery to the original owner. A second regression in `tests/pi-dispatch.mjs` failed before the sidecar repair because a partially written completion file immediately changed the ledger to `failed`; it passed after the watcher began retrying that read.

| Requirement | Evidence | Result |
|---|---|---|
| Completion during handoff reaches one owner | The cross-process test holds Herdr pane creation open, completes the worker, then starts the receiver. It observed one receiver message and zero original-owner messages after the fix; the pre-fix count was two. The ledger lock orders completion and transfer. | Local integration pass. |
| Failed handoff retains original-owner delivery | The same test completes a worker while pane creation fails. The old watcher delivered one result after the transfer rolled back, and its ledger recorded `delivered=true`. | Local integration pass. |
| A transient completion-file read preserves the worker status | `tests/pi-dispatch.mjs` held a partial `.exit` file and observed `running`, then wrote a complete `done` payload and observed one message with ledger status `done`. | Local runtime pass. |
| Existing suites remain green | `bash tests/install.sh`, `bash tests/uninstall.sh`, `bash tests/prompts.sh`, `node tests/profile.mjs`, `node --experimental-strip-types tests/pi-dispatch.mjs`, `node --experimental-strip-types tests/pi-handoff-race.mjs`, `python3 tests/pi_dispatch_cli.py`, and `python3 -m unittest tests.pi_review_fixes -q` exited 0. | Local pass. |
| Real HOME uses the repaired package | `bash scripts/install.sh --target pi` exited 0 on the real HOME. `pi list` resolves the local package to this checkout. | Installation pass. |
| An active Herdr dispatch reaches the receiver once with the correct status | A real Pi main launched active `uat-release-recon-2`, handed it to `handoff-fde124a8`, then released its wait gate. The old session persisted zero `subagent_result` and one `transferred_dispatch_notice` for dispatch `c4c4b25b-130d-4957-af5f-7e58d83fa3b8`; the receiving session persisted one `recovered_dispatch_result`. Its ledger reached `done`, `delivered=true`. The test tabs were closed. | Real Herdr pass. |

The first real handoff delivered once but incorrectly marked the completed worker `failed`. The watcher treated any unreadable completion file as a failure; the partial-file regression reproduced that path, although the first live run did not capture the exact failed read. After the retry change, the second real handoff reported `done`; the first run remains recorded as a failed status check, not a pass. The Herdr check exercised a worker completing after ownership transfer. The cross-process regression exercises completion inside the pane-creation window.

### Reflexive pass for the follow-up

- Friction: the graph trace required the full qualified name (`gap`). Action: resolved by using the identifier from `search_graph`; the existing graph guidance already states this.
- Friction: a test-only `PI_HANDOFF_ID` leaked into the next scenario (`gap`). Action: resolved by clearing it between test sessions.
- Friction: a consumed completion sidecar produced a false `failed` result (`gap`). Action: resolved in the watcher, regression test, and runtime design. No standing agent instruction changed.

## Handoff ownership commit follow-up (2026-09-25)

The earlier race follow-up above describes the pre-commit ownership model. This pass replaces that model: the original owner retains running dispatches through receiver startup and prompt submission. The atomic `state: committed` handoff file is the ownership switch.

| Requirement | Evidence | Result |
|---|---|---|
| Worker completion in every startup window reaches the current owner once | `tests/pi-handoff-windows.mjs` gated tab creation, shell readiness, agent start, receiver readiness, prompt submission, and the commit-file write while a worker completed. Each pre-commit result reached the old session once; completion while the commit lock was held, immediately after commit before receiver import, and after import reached the receiver once. The prior `tests/pi-handoff-race.mjs` was updated to assert old-owner delivery before commit. Against `049c455`, the new window test failed at tab creation because the old owner received no result; isolated start-failure and prompt-failure cases also failed. | Local cross-process pass; red on old revision. |
| Failed or partial startup retains old ownership | The window test injected tab-create failure, shell timeout, ordinary agent-start failure, missing receiver-ready marker, and prompt failure. Each case delivered once to the old session. `tests/pi_handoff_commit.py` injected pending-file and commit-file write failures; both left the old ledger running and removed the pending handoff. The old revision failed the commit-file test because it had already transferred before startup. | Local pass. |
| A committed transfer remains authoritative if the old ledger view write fails | `tests/pi_handoff_commit.py` injected a post-commit ledger write error. The handoff returned success with a warning; the committed file identified the receiver, `roll-call` showed `transferred`, and `reattach` refused the old owner. | Local pass. |
| Concurrent processes retain ledger records and deliver once | `tests/pi-ledger-concurrency.mjs` registered 16 dispatches from separate processes, sampled the ledger while writes occurred, and started two receivers for one completed dispatch. It observed 16 records, zero invalid JSON reads, and one delivery. Against `049c455`, two receivers delivered the same result. | Local cross-process pass; red on old revision. |
| A real active dispatch transfers to the receiver | After `bash scripts/install.sh --target pi` completed on the authorized real HOME, Pi source session `01a0d7cd-f852-7061-abb3-f95bba4e73a4` launched active dispatch `88a0d9bc-3779-49f7-835b-9cb08a919d00`. Handoff `2232da522c514d63bb6833ce4e5e28f7` reached `committed` with the receiver ledger `running`. After the test controller released the gate, the old session file contained one `transferred_dispatch_notice` and zero result messages; receiver session `01a0d7ce-6b8a-7583-bdc7-16349175ba2b` contained one `recovered_dispatch_result`. Its ledger recorded `done`, `delivered=true`. Following the final retry change and repeat real-HOME install, a second active dispatch `5d1678d3-9266-483c-98e4-32713bd22d95` transferred through handoff `2401fe906313476d95f7543228e3eaa9`. Before completion, the receiver ledger showed `running`; afterward, the old session had one transfer notice and zero results, while receiver session `01a0d7d9-f259-7442-a56b-4bbdcf6ee249` had one recovered result and `done`, `delivered=true`. In that second run, the receiving agent created the gate file. | Real Herdr pass on the final version. |
| A real receiver-start failure leaves the old owner receiving | A test-only PATH shim rejected `herdr agent start handoff-*` while passing through other real Herdr operations. Source session `01a0d7d0-61e2-73ce-afb5-5fe70c7357d3` launched active dispatch `304b8be9-6428-42a1-902c-6109d3012401`; its handoff failed at receiver start, and roll-call still showed `running`. After gate release, its session file contained one `subagent_result`, and its ledger recorded `done`, `delivered=true`. No committed handoff file or receiving agent remained. | Real Herdr failure-injection pass. |
| A temporary `sendMessage` failure retries the result | `tests/pi-dispatch.mjs` injected one synchronous send failure. The ledger stayed `running`, the watcher retried, and one message was delivered before the ledger became `done`. | Local runtime pass. |
| Existing behavior remains intact | `bash tests/install.sh`, `bash tests/uninstall.sh`, `bash tests/prompts.sh`, `node tests/profile.mjs`, `node --experimental-strip-types tests/pi-dispatch.mjs`, `node --experimental-strip-types tests/pi-handoff-race.mjs`, `node --experimental-strip-types tests/pi-handoff-windows.mjs`, `node --experimental-strip-types tests/pi-ledger-concurrency.mjs`, `python3 tests/pi_dispatch_cli.py`, and `python3 -m unittest tests.pi_handoff_commit tests.pi_review_fixes -q` passed after updating the old transfer-before-start assertions. `git diff --check` passed. | Local suites pass. |

The six UAT main-agent tabs and their worker tabs were closed after completion; the three temporary gate directories were removed. The real HOME Pi target remains installed. The local checks do not claim a crash-safe transaction between Pi's `sendMessage` and its durable receipt; that failure window was outside the handoff-step injection used here.

### Reflexive pass for this follow-up

- Friction: One patch attempted delete and add on the same path (`gap`). Action: resolved by retaining the original race test and adding a separate window test; no agent instruction changed.
- Friction: A local `process` binding shadowed Node's global (`gap`). Action: resolved in the test fixture; no agent instruction changed.
- Friction: Reused session IDs caused later isolated scenarios to skip startup (`gap`). Action: resolved by unique IDs in the test matrix; no agent instruction changed.
- Friction: Herdr tab environment PATH was reordered by shell startup (`gap`). Action: resolved by starting the test Pi process through `pane run` with an explicit PATH. The real failure-injection procedure is captured here; no standing agent instruction changed.
- Friction: The commit-window fixture assumed all `write_json` payloads were objects (`gap`). Action: resolved by gating only the committed handoff object; no agent instruction changed.
- Friction: The final receiver created its own test gate (`gap`). Action: recorded the actual release actor and checked ownership before and after completion; no standing agent instruction changed.

The `solid-loop` pass classified these as test or environment facts resolved by the change. The edited design section passed the no-op test: each sentence explains the ownership seam, failure boundary, or verification surface.

## Appropriateness review

The implementation delegates dispatch, intercom, ask, todo, MCP, Claude bridge, and aaaav validation to their packages. Local code covers the three approved gaps: durable dispatch recovery, handoff, and shipping guidance. The default legacy install path remains available. Upstream measured Opus 5.5 1M on Max with Extra Usage off; Pro remained unmeasured in the cited commit. The local model catalog reports 1M, while a full-context request on this user's subscription remains untested.

## Reflexive friction classification

- Friction: A recursive cleanup command was rejected by command review (`gap`). Action: resolved by using temporary directory scopes in the test; no agent instruction applies.
- Friction: Filesystem notification timing made an immediate sidecar assertion unreliable (`gap`). Action: resolved by a periodic sidecar check and bounded test wait.
- Friction: Pi's model catalog lived in a nested dependency rather than a top-level package (`gap`). Action: resolved by reading the nested catalog; no standing instruction is needed.
- Friction: Pi bash did not expose a reliable main session ID for recovery commands (`gap`). Action: resolved by the extension's `dispatch_control` tool, which supplies the session ID from Pi's API.
- Friction: A mutable model-config reference prevented faithful uninstall restoration (`gap`). Action: resolved by copying the original model config and verifying restoration under a temporary HOME.
- Friction: The generated config lacked `status.enabled`, which `pi-herdr-agents` requires to load (`gap`). Action: resolved by setting and restoring the status config, then loading the actual package against generated temporary-HOME config.
- Friction: `pi-herdr-agents` consumes a completed worker's `.exit` sidecar during normal delivery, leaving an extension ledger row marked `running` after parent restart (`gap`). Action: resolved by reconciling the parent's persisted `subagent_result` before observing unfinished workers and before ledger tools run; verified in Herdr.
- Friction: A new Herdr tab returned before its shell accepted `agent start`, and a default tab could land in another workspace (`gap`). Action: resolved by choosing `HERDR_WORKSPACE_ID`, waiting for the new shell, and exercising a real receiving main pane.

## Receiver resume and reattach follow-up (2026-09-25)

The receiver-crash regression killed the first process after the handoff became committed and before it imported a dispatch. It failed against `8c7e48d` because the resumed session had no ledger. The reattach regression failed against that revision because a concurrent `done` update was overwritten with `running`. The committed-marker check also failed because the CLI removed the receiver's `.ready` file.

| Requirement | Evidence | Result |
|---|---|---|
| A receiver restarted after commitment imports its assigned dispatch without the first process's environment variable | `node --experimental-strip-types tests/pi-handoff-resume.mjs` killed the first receiver with `SIGKILL`, restarted the same session without `PI_HANDOFF_ID`, and observed one imported worker, one result, and no unrelated handoff. In a real Herdr tab, Pi session `f9a94ee2-8c36-499c-b1e5-e840672ec95a` first wrote a session file, then was killed after commit with no receiver ledger. A new Pi process resumed that file without `PI_HANDOFF_ID`, recorded `herdr-final-worker` as `done`, `delivered=true`, emitted one `recovered_dispatch_result`, and received a successful `gpt-6-luna` response containing the test result. See `/Users/weihung/.straw-boss/plans/pi-migration/artifacts/f4-herdr-resume-uat.json`. | pass |
| A committed handoff retains the receiver's session binding until a restart can find it | `test_committed_handoff_keeps_receiver_session_marker` observed `transfer.ready` containing `receiver` after the CLI committed the handoff. | pass |
| Reattach preserves a concurrent owner-ledger status update | `test_reattach_preserves_concurrent_ledger_update` changed the worker to `done` while pane creation was in progress. Reattach reread under the owner lock, closed the provisional pane, raised a changed-state error, and left the ledger `done`. | pass |
| Cross-process crash delivery semantics are recorded | Both Pi handoff and dispatch-recovery skills, the approved spec, and the design state that a crash between result send and receipt can cause redelivery, with at-least-once delivery across a process crash. The accepted window received documentation only. | pass |
| Repository suites and real Pi installation remain usable | `bash tests/install.sh`, `bash tests/uninstall.sh`, `bash tests/prompts.sh`, `node tests/profile.mjs`, the four existing Pi runtime suites, the new resume test, `python3 tests/pi_dispatch_cli.py`, and `python3 -m unittest tests.pi_handoff_commit tests.pi_review_fixes -q` exited 0. `bash scripts/install.sh --target pi` completed on the authorized real HOME. | pass |

The first isolated Herdr check imported the result but its model turn reported `Unknown provider: unknown`. The final check supplied the installed Codex authentication to the isolated test process, persisted a Pi session file before the crash, and observed a successful model response after resume. The accepted send-to-receipt crash window was documented rather than fault injected.

### Reflexive pass for this follow-up

- Friction: the combined graph regex returned no recovery symbols (`gap`). Action: the concept query found exact names; this was a query choice, so no standing instruction changed.
- Friction: isolated Pi lacked a default model (`gap`). Action: the final run used an explicit Codex model and the installed authentication; the first run remains recorded, so no standing instruction changed.
- Friction: zsh noclobber rejected a reused RPC log path (`gap`). Action: the test used a fresh log path; no standing instruction changed.
- Friction: Pi RPC name and bash commands did not persist a session file (`gap`). Action: the final run used an authenticated prompt before killing Pi and resumed the resulting session file; no standing instruction changed.

The `solid-loop` pass classified these as local discovery and test-environment facts. The skill edits passed the no-op check: each sentence states the ownership or delivery behavior a recovering agent needs.

## Settled compaction and null restoration follow-up (2026-09-25)

| Requirement | Evidence | Result |
|---|---|---|
| Compaction checks after Pi finishes a turn | `tests/pi-idle-compaction.mjs` emits `agent_end`, waits 130 ms while active, then emits `agent_settled` and observes one compaction above 300,000 tokens. The test failed before the fix because no `agent_settled` handler existed and passed afterward. The installed Pi type declaration defines `agent_settled` as the point after retries, compaction, and queued continuations finish. | Local event-order pass; a live 300,000-token session was not constructed. |
| Uninstall restores settings that previously contained JSON `null` | `test_uninstall_restores_present_null_settings` starts with `defaultProvider: null` and `theme: null`, installs twice, uninstalls, and observes both keys still present with null values while an originally absent key stays absent. It failed before the fix because `defaultProvider` disappeared and passed afterward. | Local install/uninstall pass. |
| Powerline queue uses its declared setting | `scripts/pi-target.py` now applies `POWERLINE_QUEUE` at the write site; the installer and uninstall suites passed. | Source review and local suites pass. |
| Repository checks and real HOME load | `bash tests/install.sh`, `bash tests/uninstall.sh`, `bash tests/prompts.sh`, `node tests/profile.mjs`, all six Pi runtime suites including idle compaction, `python3 tests/pi_dispatch_cli.py`, and `python3 -m unittest tests.pi_handoff_commit tests.pi_review_fixes -q` exited 0. `bash scripts/install.sh --target pi` completed on the authorized real HOME. Pi RPC started with the installed configuration, returned a `get_state` response, and exited 0 with empty stderr and no error event. `git diff --check` passed. | Local suites, real installation, and extension startup pass. |

Existing install markers did not record whether a prior null-valued key existed. The real HOME marker uses that older format, so uninstall of a preexisting null value cannot be inferred from it. New installs record key presence; old markers retain their prior restoration behavior.

Reflexive: the Pi event-definition lookup first used an agent-local npm path, then the active Node version's global npm root. This was a tool-use gap with no standing instruction to change; the `solid-loop` pass made no instruction edit.

## Port review fixes (2026-09-25)

| Requirement | Evidence | Result |
|---|---|---|
| External-install regression tests pass again | `tests/pi_review_fixes.py` fixtures now produce what a successful install leaves: the team-toon-tack package with its skill and `ttt` CLI under the npm prefix, and a codebase-memory binary that writes the official Pi resources. `test_external_git_switch_keeps_the_new_checkout` and `test_failed_external_install_can_retry_and_uninstall` pass. | pass |
| Safety gate blocks malformed exit-0 output | `pi/extensions/mp-infra-hooks.ts` parses stdout only. Empty stdout allows the command. Non-empty stdout that is not JSON blocks it, and the reason includes that output. `tests/pi-mp-infra-hooks.mjs` points the gate at a fake hook. Empty output returns allow, and `Traceback: not json` blocks with that text. The malformed assertion failed against the previous extension. | pass |
| Repository suites and real install | `bash tests/install.sh`, `bash tests/uninstall.sh`, `bash tests/prompts.sh`, `node tests/profile.mjs`, all seven `tests/pi-*.mjs` suites, `python3 tests/pi_dispatch_cli.py`, `python3 tests/pi_port_install.py`, and `python3 -m unittest tests.pi_handoff_commit tests.pi_review_fixes -q` exited 0. `git diff --check` passed. `bash scripts/install.sh --target pi` completed on the authorized real HOME. | pass |


Main-agent follow-up after fresh-context review (2026-09-25): restored four rules the rewrite had dropped or weakened — fail fast instead of silent degradation (Work), worktree workers keep their checkout for main-session review (Model and dispatch), gather related pending decisions into one `ask_user` round (Model and dispatch), and no mocks in delivered code (Verification and delivery).
