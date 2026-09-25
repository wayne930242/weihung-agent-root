# Pi harness migration design

The approved contract is [spec.md](spec.md). Package behavior and user choices are in [decision.md](decision.md).

## Install seam

`scripts/install.sh` and `scripts/uninstall.sh` keep their existing default target set (`claude,codex,gemini`). The `--target` parser expands repeated and comma-separated values, with `full` selecting all four. Existing operations are grouped by target. The shared `~/.agents/skills` links remain installed while either Codex or pi is selected; removing one target retains links needed by the other.

The pi target writes only pi-owned configuration: expanded `~/.pi/agent/AGENTS.md`, Pi package registrations, the MCP adapter's host discovery setting, and generated model routing. External installation uses `pi install` for the six community packages and local aaaav package. The bridge is pinned to upstream git commit `227f5eb4450a070dfbc083a7fe75b8b35366b941` until npm includes #120; an existing npm bridge registration is retired during install and restored on uninstall. `--skip-external` exercises configuration without npm or Herdr mutation. The pi CLI and Herdr integration are installed on a real external run. Removing pi removes only this repo's configuration and package registrations; the pi binary and authentication remain.

Pi identifies git packages by repository when installing or removing them. Switching bridge commits replaces the installed checkout, so this installer removes an obsolete git registration from settings by exact source string after the new commit is installed. Uninstall removes the pinned checkout and restores the preexisting git source.

## Runtime seam

`pi-herdr-agents` owns pane dispatch, fallback attempts, and result delivery. `pi-intercom` owns peer discovery and messages. `pi-ask-user`, `@capdiem/pi-todo`, `pi-mcp-adapter`, `pi-claude-bridge`, and the aaaav package retain their own behavior. This repo adds the three missing workflows as a small Pi extension and skills: durable dispatch inventory and reattachment after parent restart, coordinated handoff into a new Herdr pane, and Git shipping through the target repository's conventions. They call the package interfaces rather than duplicate their runtime.

An active handoff marks the old ledger `transferred` before the receiver starts. The package's original watcher still runs in the old Pi process, so the local extension changes its completed `subagent_result` to a transfer notice before it enters the old model context. It forwards the result through an agent-local sidecar; the receiver also watches the worker's completion sidecar and delivers whichever result appears first. A delivered marker prevents a late original result from recreating a forwarded payload.

## Model routing

The active strategy is read from `skills/managing-model-preferences/model-preference-profile.md`. A profile application script maps its tier rows to Pi `provider/model-id` references and thinking levels, writes Pi's default model and thinking, and writes `pi-herdr-agents` task candidates. A fallback list pairs a Claude bridge model with the matching Codex tier. The model preference skill runs the same script after a strategy switch.

`pi-herdr-agents` accepts six task categories: coding, review, recon, qa, architecture, and docs. The remaining profile tiers use explicit ordered model lists in the generated Pi instructions; the subagent call passes that list and its thinking level. The default candidate list removes duplicate models.

## Verification

Shell tests run with an isolated HOME, stub external commands, and inspect per-target files, preservation of other targets, uninstall behavior, and a repeated run. Runtime verification occurs after the user's real-HOME checkpoint. The Herdr session checks package loading, MCP access, dispatch, restart recovery, intercom, handoff, shipping, strategy switching, and aaaav hook feedback. Each claim is recorded separately in `verification.md`.

## Friction Notes

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
