# Pi harness migration design

The approved contract is [spec.md](spec.md). Package behavior and user choices are in [decision.md](decision.md).

## Install seam

`scripts/install.sh` and `scripts/uninstall.sh` keep their existing default target set (`claude,codex,gemini`). The `--target` parser expands repeated and comma-separated values, with `full` selecting all four. Existing operations are grouped by target. The shared `~/.agents/skills` links remain installed while either Codex or pi is selected; removing one target retains links needed by the other.

The pi target writes only pi-owned configuration: expanded `~/.pi/agent/AGENTS.md`, Pi package registrations, the MCP adapter's host discovery setting, and generated model routing. External installation uses `pi install` for the six community packages and local aaaav package. `--skip-external` exercises configuration without npm or Herdr mutation. The pi CLI and Herdr integration are installed on a real external run. Removing pi removes only this repo's configuration and package registrations; the pi binary and authentication remain.

## Runtime seam

`pi-herdr-agents` owns pane dispatch, fallback attempts, and result delivery. `pi-intercom` owns peer discovery and messages. `pi-ask-user`, `@capdiem/pi-todo`, `pi-mcp-adapter`, `pi-claude-bridge`, and the aaaav package retain their own behavior. This repo adds the three missing workflows as a small Pi extension and skills: durable dispatch inventory and reattachment after parent restart, coordinated handoff into a new Herdr pane, and Git shipping through the target repository's conventions. They call the package interfaces rather than duplicate their runtime.

## Model routing

The active strategy is read from `skills/managing-model-preferences/model-preference-profile.md`. A profile application script maps its tier rows to Pi `provider/model-id` references and thinking levels, writes Pi's default model and thinking, and writes `pi-herdr-agents` task candidates. A fallback list pairs a Claude bridge model with the matching Codex tier. The model preference skill runs the same script after a strategy switch.

## Verification

Shell tests run with an isolated HOME, stub external commands, and inspect per-target files, preservation of other targets, uninstall behavior, and a repeated run. Runtime verification occurs after the user's real-HOME checkpoint. The Herdr session checks package loading, MCP access, dispatch, restart recovery, intercom, handoff, shipping, strategy switching, and aaaav hook feedback. Each claim is recorded separately in `verification.md`.

## Friction Notes

- Tried: an isolated-HOME smoke test that removed its temporary directory with `rm -rf`.
  Found: command review rejected the cleanup command; a Python `TemporaryDirectory` scope provides bounded cleanup.
  Led by: aaaav-do's isolated reality anchor.
- Tried: recovery delivery using only a directory watcher and a fixed 100 ms assertion.
  Found: filesystem notifications may arrive later or be missed; a bounded retry in the test and periodic sidecar check make recovery observable.
  Led by: aaaav-do's restart recovery anchor.
- Tried: reading Pi's model catalog from a top-level `pi-ai` installation.
  Found: Pi 0.87.1 nests `pi-ai` under its own package; the nested `openai-codex.json` confirms the GPT-6 model IDs and supported thinking levels.
  Led by: managing-model-preferences' model verification instruction.
