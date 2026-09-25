# Pi harness migration design

The approved contract is [spec.md](spec.md). Package behavior and user choices are in [decision.md](decision.md).

## Install seam

`scripts/install.sh` and `scripts/uninstall.sh` keep their existing default target set (`claude,codex,gemini`). The `--target` parser expands repeated and comma-separated values, with `full` selecting all four. Existing operations are grouped by target. The shared `~/.agents/skills` links remain installed while either Codex or pi is selected; removing one target retains links needed by the other.

The pi target writes only pi-owned configuration: expanded `~/.pi/agent/AGENTS.md`, Pi package registrations, the MCP adapter's host discovery setting, and generated model routing. External installation uses `pi install` for the six community packages and local aaaav package. The bridge is pinned to upstream git commit `227f5eb4450a070dfbc083a7fe75b8b35366b941` until npm includes #120; an existing npm bridge registration is retired during install and restored on uninstall. `--skip-external` exercises configuration without npm or Herdr mutation. The pi CLI and Herdr integration are installed on a real external run. Removing pi removes only this repo's configuration and package registrations; the pi binary and authentication remain.

Pi identifies git packages by repository when installing or removing them. Switching bridge commits replaces the installed checkout, so this installer removes an obsolete git registration from settings by exact source string after the new commit is installed. Uninstall removes the pinned checkout and restores the preexisting git source.

## Runtime seam

`pi-herdr-agents` owns pane dispatch, fallback attempts, and result delivery. `pi-intercom` owns peer discovery and messages. `pi-ask-user`, `@capdiem/pi-todo`, `pi-mcp-adapter`, `pi-claude-bridge`, and the aaaav package retain their own behavior. This repo adds the three missing workflows as a small Pi extension and skills: durable dispatch inventory and reattachment after parent restart, coordinated handoff into a new Herdr pane, and Git shipping through the target repository's conventions. They call the package interfaces rather than duplicate their runtime.

The handoff interface is `dispatch_control` plus an immutable handoff ID. The Python CLI writes a pending file, creates the pane, starts the receiving Pi agent, waits for the extension's ready marker, and submits the scope prompt. The old owner keeps every active dispatch through these steps. Under its ledger lock, the CLI then reads the still-running records and atomically replaces the pending file with a committed handoff file. This file is the ownership decision: completion before its replacement reaches the old session; completion afterward reaches the receiver. The old ledger's `transferred` status is a repairable view. A write failure in that view reports a warning and leaves the committed handoff authoritative. Pane, shell, start, readiness, prompt, or pending/commit-file failures leave ownership with the old session.

The Pi extension imports records only after commitment. Its readiness marker binds the handoff to the receiving session and remains after commit until that session durably imports the records, so a restarted receiver imports the committed file without the first process's `PI_HANDOFF_ID`. The startup import poll keeps the Python CLI independent of Pi session timing. The old process's `pi-herdr-agents` watcher still emits a native result, so the extension replaces it with a transfer notice and forwards the payload through an agent-local sidecar. The receiver watches that sidecar and the worker completion file. Atomic ledger replacement and directory locks cover concurrent processes; reattach rereads and updates its ledger under the owner lock after pane creation. A per-dispatch delivery lock and marker allow one recovered delivery across live receivers. The completion watcher retries a temporarily unreadable sidecar while the package consumes or replaces it. A crash after sending a result but before recording its receipt permits one replay after restart.

The previous shape transferred the old ledger before pane creation and then rolled it back on selected failures. That made each later startup step a separate recovery case. The committed-file shape has one ownership transition after the receiver is ready, and `roll-call` derives stale old-ledger status from that file. The Python CLI and Pi extension occupy the existing dispatch-control seam; callers still use one `handoff` action. Tests exercise the CLI boundary with Herdr fault injection, the extension's result hooks, and real Herdr sessions.

## Model routing

The active strategy is read from `skills/managing-model-preferences/model-preference-profile.md`. A profile application script maps its tier rows to Pi `provider/model-id` references and thinking levels, writes Pi's default model and thinking, and writes `pi-herdr-agents` task candidates. A fallback list pairs a Claude bridge model with the matching Codex tier. The model preference skill runs the same script after a strategy switch.

`pi-herdr-agents` accepts six task categories: coding, review, recon, qa, architecture, and docs. The remaining profile tiers use explicit ordered model lists in the generated Pi instructions; the subagent call passes that list and its thinking level. The default candidate list removes duplicate models.

## Verification

Shell tests run with an isolated HOME, stub external commands, and inspect per-target files, preservation of other targets, uninstall behavior, and a repeated run. Runtime verification occurs after the user's real-HOME checkpoint. The Herdr session checks package loading, MCP access, dispatch, restart recovery, intercom, handoff, shipping, strategy switching, and aaaav hook feedback. Each claim is recorded separately in `verification.md`.

## Pi interface and idle compaction follow-up

The Pi target writes `panes.mode: split` and `panes.direction: right` to the existing `pi-herdr-agents` config. It records prior values in the install marker so uninstall restores them. It installs `pi-powerline-footer` and `catppuccin-pi-theme`, selects `catppuccin-mocha`, and sets Powerline's compact prompt mode to `native`. The terminal and Powerline settings are restored at their managed leaf keys, preserving other user settings. Package declarations are placed in a stable order after each install.

The repository Pi package loads `idle-compaction.ts`. Its `agent_end` and `session_start` checks run after a short settlement delay, then require idle state, no pending messages, and more than 300,000 estimated tokens. An in-flight guard prevents a second request until the compaction callback completes. The extension calls Pi's own compaction API, retaining the bridge and native auto-compaction paths.

## Claude plugin ports into Pi

The Pi target runs codebase-memory-mcp's official Pi installer in a temporary HOME, copies its generated extension and skill, and substitutes the target HOME's installed binary path for the temporary path embedded in the generated extension. The installer keeps sole ownership of `~/.pi/agent/AGENTS.md`; its existing Code discovery section supplies the instructions. The extension and skill are tracked in the Pi target marker for repeat install and uninstall.

The mp-infra port links skills from the live `moldplan-center/plugins/waydosoft-marketplace/plugins/mp-infra` checkout and records that checkout in `~/.pi/agent/mp-infra.json`. The Pi extension invokes the plugin's original hooks: the Bash pre-call gate maps block and review decisions to Pi's tool-call result and UI confirmation, the session-start check enters model context, and edit/write validators append their output to the tool result. The Nomad hook configuration selects `.nomad.j2`, while its script validates `.nomad` and `.hcl`; Pi also invokes it for those supported file types. The checkout currently contains 14 skills; the earlier scope inventory counted 13.

The team-toon-tack port installs the latest npm package under a private HOME prefix, links its CLI into `~/.local/bin/ttt`, links its skill, and generates Pi prompt templates for its 12 commands. Templates refer to the installed command source and pass Pi's `$ARGUMENTS` through to the `ttt` CLI workflow. Reapplying the target refreshes both external sources. Uninstall removes only paths recorded by the Pi target marker and restores backed-up user files.

## Friction Notes

- Tried: passing the post-edit input's top-level `file_path` to the mp-infra validator.
  Found: the Pi adapter wraps that path under `tool_input`, so the validator received no file path and the output test failed.
  Led by: the hook port's model-facing output anchor.
- Tried: resolving the private-prefix `ttt` CLI at `<prefix>/bin/ttt`.
  Found: npm's local prefix puts executable links at `<prefix>/node_modules/.bin/ttt`; the first real-HOME install stopped after creating the other port resources.
  Led by: the approved real-HOME install anchor.
- Tried: applying the Claude Nomad hook's `.nomad.j2` matcher as the only Pi trigger.
  Found: the original validator script checks only `.nomad` and `.hcl`, so that matcher produces no validation output.
  Led by: the hook-effect contract.
- Tried: capturing the first install's exit code in zsh variable `status`.
  Found: zsh reserves `status` as read-only; reading the install log exposed the actual npm prefix error.
  Led by: none.

- Tried: filtering `npm search --json` with a Python one-liner containing escaped quote characters.
  Found: the extra escaping produced a Python syntax error; a plain JSON parser returned the theme package list.
  Led by: none.
- Tried: reapplying the real-HOME Pi target and comparing managed file hashes immediately after the first update.
  Found: Pi's package installer reordered `settings.json` once; canonicalizing managed package order at the end of install makes the next run byte stable.
  Led by: aaaav-do's idempotent install reality anchor.
- Tried: saving the Herdr pane layout after a short worker completed.
  Found: automatic pane cleanup had reduced the tab to one pane; the active-worker layout was captured during a second run.
  Led by: aaaav-do's human pane-capture anchor.

- Tried: an isolated-HOME smoke test that removed its temporary directory with `rm -rf`.
  Found: command review rejected the cleanup command; a Python `TemporaryDirectory` scope provides bounded cleanup.
  Led by: aaaav-do's isolated reality anchor.
- Tried: injecting a failing npm command through the full `scripts/install.sh --target pi` path.
  Found: that path also runs codebase-memory setup before the Pi target; invoking `scripts/pi-target.py` directly isolates the external Pi failure and keeps the regression test bounded.
  Led by: aaaav-do's red-capable loop instruction.
- Tried: recovery delivery using only a directory watcher and a fixed 100 ms assertion.
  Found: filesystem notifications may arrive later or be missed; a bounded retry in the test and periodic sidecar check make recovery observable.
  Led by: aaaav-do's restart recovery anchor.
- Tried: reading Pi's model catalog from a top-level `pi-ai` installation.
  Found: Pi 0.87.1 nests `pi-ai` under its own package; the nested `openai-codex.json` confirms the GPT-6 model IDs and supported thinking levels.
  Led by: managing-model-preferences' model verification instruction.
- Tried: writing every profile tier under `models.tasks`.
  Found: `pi-herdr-agents` rejects task keys outside its six fixed categories and Pi cannot load the extension. The remaining tiers need explicit model lists in generated instructions.
  Led by: aaaav-do's real Herdr reality anchor.
- Tried: starting a new Herdr agent as soon as its pane showed a foreground shell.
  Found: Herdr can still report `agent_pane_busy` until that shell reaches its prompt; a bounded retry on that specific state lets handoff proceed.
  Led by: aaaav-do's active-dispatch handoff anchor.
- Tried: matching a shortened design sentence while appending these notes.
  Found: the existing paragraph begins with the active strategy source, so the exact patch context needed that full sentence.
  Led by: aaaav-do's friction-note instruction.
- Tried: transferring the old ledger before launching the receiver and relying on the receiver's sidecar watcher.
  Found: `pi-herdr-agents` keeps its own live watcher in the old process, so both Pi sessions received a full result. Intercepting the old custom message and forwarding its content made the new session the only model context with the result.
  Led by: aaaav-do's real active-dispatch handoff anchor.
- Tried: removing an obsolete git bridge registration through `pi remove` after installing the pinned commit.
  Found: Pi matches git package removal by repository rather than commit, which would also remove the new checkout. Exact settings cleanup preserves the pinned checkout.
  Led by: aaaav-do's package identity regression check.
- Tried: tracing `scripts.pi-dispatch.handoff` through the code graph with a shortened qualified name.
  Found: the graph requires the complete qualified name returned by `search_graph`; the exact symbol resolved the trace.
  Led by: the project graph-discovery instruction.
- Tried: reusing the first handoff's test process environment for a failed-handoff scenario.
  Found: `PI_HANDOFF_ID` imported the earlier transfer into the second test session; clearing that test-only variable isolated the owner.
  Led by: aaaav-do's red-capable handoff test.
- Tried: accepting the first real Herdr delivery as complete based on its single result message.
  Found: the worker succeeded but the receiver marked it `failed`; the watcher mapped transient unreadable completion files to failure, and a partial-file regression reproduced that path. The recovery watcher now waits for a readable sidecar or forwarded result.
  Led by: aaaav-do's real Herdr handoff anchor.
- Tried: replacing the race test in one patch with a delete and add for the same path.
  Found: the patch tool rejects multiple operations on one path in a single patch. A separate window-matrix test kept the existing regression focused.
  Led by: aaaav-do's red-capable test loop.
- Tried: naming the spawned child process `process` inside a Node test function.
  Found: the local binding shadowed Node's global `process` before initialization. A distinct `handoffProcess` name fixed the fixture.
  Led by: aaaav-do's failure-window test.
- Tried: reusing one Pi session ID for every isolated window scenario.
  Found: the extension's process-local session set treated later scenarios as repeat startups. Unique session IDs made each scenario independent.
  Led by: aaaav-do's failure-window test.
- Tried: putting the Herdr failure shim in a new tab's environment.
  Found: shell startup moved `/opt/homebrew/bin` ahead of that path. Starting Pi through `herdr pane run` with an explicit leading PATH exercised the intended agent-start failure.
  Led by: aaaav-do's real Herdr failure anchor.
- Tried: gating every Python `write_json` call as if its data were an object.
  Found: ledger writes pass a list. The test fixture now gates only dictionary data with `state: committed`.
  Led by: aaaav-do's commit-window failure injection.
- Tried: directing only the source agent to leave the final UAT gate closed.
  Found: the receiving agent inferred that it should create the release file from the handoff summary. The final check records that actor and verifies the ledger was running before completion.
  Led by: aaaav-do's final real Herdr anchor.
- Tried: finding the recovery functions with a combined graph name and file regex.
  Found: that query returned no symbols; a concept query returned the exact qualified names for tracing and source inspection.
  Led by: the project graph-discovery instruction.
- Tried: running the resumed-receiver Herdr check with an isolated Pi agent directory and its default model.
  Found: Pi imported the dispatch and persisted the recovered result, then its model turn reported `Unknown provider: unknown` because the isolated directory had no model profile.
  Led by: aaaav-do's real Herdr anchor.
- Tried: reusing the first Pi RPC log path for a second Herdr test command.
  Found: the tab's zsh noclobber setting rejected the redirection. A fresh log path let the command run.
  Led by: aaaav-do's real Herdr anchor.
- Tried: persisting a Pi receiver session with RPC `set_session_name` and `bash` commands.
  Found: neither wrote a session file. An authenticated prompt produced the file required for a true `--session` restart.
  Led by: aaaav-do's resumed-session anchor.
