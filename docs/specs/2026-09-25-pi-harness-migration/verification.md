# Pi harness migration verification

Status: local implementation verified; real HOME checkpoint pending. These observations do not establish a completed migration.

| Spec | Evidence | Result |
|---|---|---|
| 1. Install targets | `bash tests/install.sh`; the target matrix exercised default, each target, repeated Pi install, `full`, and generated settings under temporary HOME. A separate temporary-agent Pi RPC load exited without extension errors. | Local pass; real HOME pending. |
| 2. Uninstall targets | `bash tests/uninstall.sh` and target matrix; Pi uninstall retained preexisting packages and restored a preexisting `AGENTS.md` and `herdr-agents` model config. | Local pass; real HOME pending. User owns when old targets are removed. |
| 3. Session resources | An isolated Pi package load registered six community packages plus aaaav and this repo; Pi RPC started without extension errors. Generated instructions expanded all shared imports and enabled MCP host discovery. | Package load pass; Herdr session, both model turns, OAuth MCP, and status reporting pending. |
| 4. Dispatch | `pi-herdr-agents` package and tier candidates are configured; the package had a successful cross-repo Herdr dispatch during prerequisite research. | Migration-specific dispatch, tier, fallback, worker permissions, and delivery pending. |
| 5. Recovery | `node --experimental-strip-types tests/pi-dispatch.mjs` exercised parent restart, child sidecar completion, and delivered result. `python3 tests/pi_dispatch_cli.py` exercised roll-call and reattach with mocked Herdr. | Local pass; real pane restart and reattachment pending. |
| 6. Inter-main coordination | `pi-intercom` was included in the isolated package load; the CLI test exercised handoff with mocked Herdr. | Real peer discovery, message delivery, and new-pane handoff pending. |
| 7. Shipping | The local Pi package exposes `shipping-task` in an isolated load. | Target app branch, commit, PR, CI, and merge workflow pending an approved real task. |
| 8. Model profile | Temporary HOME test applied the active profile and restored previous settings on uninstall. `node tests/profile.mjs` passed. User confirmed Gemini/agy to Codex Luna and former 1M tiers to bridge Opus 5.5 200K. | Local config pass; live Pi reload and dispatch parameter checks pending. |
| 9. aaaav | The adjacent aaaav package has a Pi manifest and loaded in isolated Pi. | Real write/edit `validate_tool_use` feedback pending. |

Additional checks: `bash tests/prompts.sh`, `git diff --check`, the Pi recovery extension RPC load, and the actual `pi-herdr-agents` extension load against generated temporary-HOME config passed. The real HOME install is the next checkpoint under the approved spec. Pi has no `openai-codex` login in the current HOME, so a live Codex model turn requires the user to run `/login` in Pi.

The model-preference skill applies local Pi settings when it switches strategies. The separate web console currently updates the strategy entrypoint through its remote repository flow; it does not run the local Pi profile application script. A web-console switch therefore needs a local `apply-profile` run before the next Pi dispatch.

## Appropriateness review

The implementation delegates dispatch, intercom, ask, todo, MCP, Claude bridge, and aaaav validation to their packages. Local code covers the three approved gaps: durable dispatch recovery, handoff, and shipping guidance. The default legacy install path remains available. The approved Opus 5.5 200K choice reduces context capacity for formerly 1M tiers and must be visible during live use.

## Reflexive friction classification

- Friction: A recursive cleanup command was rejected by command review (`gap`). Action: resolved by using temporary directory scopes in the test; no agent instruction applies.
- Friction: Filesystem notification timing made an immediate sidecar assertion unreliable (`gap`). Action: resolved by a periodic sidecar check and bounded test wait.
- Friction: Pi's model catalog lived in a nested dependency rather than a top-level package (`gap`). Action: resolved by reading the nested catalog; no standing instruction is needed.
- Friction: Pi bash did not expose a reliable main session ID for recovery commands (`gap`). Action: resolved by the extension's `dispatch_control` tool, which supplies the session ID from Pi's API.
- Friction: A mutable model-config reference prevented faithful uninstall restoration (`gap`). Action: resolved by copying the original model config and verifying restoration under a temporary HOME.
- Friction: The generated config lacked `status.enabled`, which `pi-herdr-agents` requires to load (`gap`). Action: resolved by setting and restoring the status config, then loading the actual package against generated temporary-HOME config.
