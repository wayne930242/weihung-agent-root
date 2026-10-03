# weihung-agent-root

Personal user-root setup for [pi](https://www.npmjs.com/package/@earendil-works/pi-coding-agent). This repository is the source of truth for pi's user instructions, model routing, packages, skills, rules, and local extensions on every machine. It supports only pi; the last version that also configured Claude Code, Codex, and Gemini is the `legacy-claude-codex` tag.

Claude models reach pi through `pi-claude-bridge`, which runs on the machine's Claude Code installation and login. Nothing in this repository configures Claude Code itself.

## New machine

Prerequisites: Node.js with npm, Python 3, Git, Herdr, and Claude Code logged in with the account that should serve Claude models.

```bash
git clone https://github.com/wayne930242/weihung-agent-root ~/projects/weihung-agent-root
cd ~/projects/weihung-agent-root
bash scripts/install.sh
```

Then start `pi` inside Herdr and run `/login` for OpenAI Codex. Claude models need no pi login; the bridge uses Claude Code's. For browser work in your own Chrome, install the [Playwriter extension](https://chromewebstore.google.com/detail/playwriter/jfeammnjpkecdekppnclgkkffahnhfhe); clicking its icon on a tab hands that tab to agents, and clicking again takes it back.

Clone beside the related checkouts when they exist: the installer uses `~/projects/aaaav` when present (otherwise `github.com/wayne930242/aaaav`) and the mp-infra and sdlc plugins from `~/projects/moldplan-center` (or `PI_MP_INFRA_ROOT`, `PI_SDLC_ROOT`).

To test an unreleased `pi-herdr-agents` fix, set `PI_HERDR_AGENTS_ROOT` to a checkout of it (its `package.json` must be named `pi-herdr-agents`): the installer then registers that directory instead of the pinned npm release, never both, and fails when the variable points at a missing directory or another package. Unset it and re-run to return to the pinned release. The variable is not auto-detected and exists only for testing: once the upstream release carrying the fix is pinned in `PACKAGES`, stop using it. The `agents/` overrides match the pinned release's bundled roles, so compare them with the checkout's `agents/` when it differs.

Installer options:

- `--home PATH` installs into another home directory, for example a throwaway smoke test.
- `--skip-external` writes configuration only: no npm, pi package, Herdr, or network installs.
- `--force` backs up conflicting targets to `~/.local/state/weihung-agent-root/backups/<timestamp>/` before replacing them. Without it, a conflict stops the install.

A machine set up before the pi-only change still has the Claude Code, Codex, and Gemini links from that version. Remove them first with the legacy uninstaller: `git worktree add /tmp/legacy legacy-claude-codex && bash /tmp/legacy/scripts/uninstall.sh --target claude,codex,gemini`, then `git worktree remove /tmp/legacy`.

The installer is idempotent; re-run it after pulling changes. `bash scripts/uninstall.sh` (same `--home` and `--skip-external` options) removes this repository's links, packages, generated instructions, and settings, and restores what the install backed up. The pi binary and its logins stay.

## What the install sets up

`scripts/install.sh` links the repository into the home directory and runs `scripts/pi-target.py install`, which:

- installs or upgrades pi (`npm install -g @earendil-works/pi-coding-agent`) and runs `herdr integration install pi`, which reports each pi session's state to Herdr;
- installs the pinned [Playwriter](https://github.com/remorses/playwriter) CLI (`npm install -g playwriter@0.7.0`), which drives the user's own Chrome through the Playwriter extension; uninstall removes it only when this install added it;
- installs the pi packages below, aaaav, straw-boss, and this repository as a local pi package;
- generates `~/.pi/agent/AGENTS.md` from [pi/AGENTS.md.in](pi/AGENTS.md.in);
- sets UI settings, `pi-herdr-agents` pane placement and models, and MCP host-config discovery;
- ports resources pi cannot install as packages: team-toon-tack and pi-skills.

Every file it writes is recorded in `~/.pi/agent/.weihung-agent-root.json`, so uninstall removes exactly those files and restores the previous settings values.

### Links

| Home path | Source |
|---|---|
| `~/.agents/skills/<name>` | [skills/](skills/): `providing-knowledge`, `publishing-pi-extensions`, `reflecting-to-root`, `using-sessionflow`, `writing-in-weihung-voice` |
| `~/.pi/agent/rules` | [rules/](rules/): user-global rules |
| `~/.pi/agent/agents` | [agents/](agents/): global overrides of the `pi-herdr-agents` 2.0.4 bundled roles. Each file is the bundled role with its `tools:` allowlist removed, so a child loads every installed tool; the bundled `spawning:` policy still limits nested subagents. Re-derive them when the `pi-herdr-agents` pin changes. |
| `~/.pi/agent/skills/pi-skills` | A clone of [badlogic/pi-skills](https://github.com/badlogic/pi-skills) in `~/.local/share/weihung-agent-root/pi-skills`, pulled on each install. Its skills (`brave-search`, `browser-tools`, `gccli`, `gdcli`, `gmcli`, `transcribe`, `vscode`, `youtube-transcript`) need their own CLIs or keys as each `SKILL.md` describes. |

### Packages

Registry packages are pinned to exact versions in [scripts/pi_root/pins.py](scripts/pi_root/pins.py), so every machine installs the same release and `pi update` leaves them alone. `python3 scripts/pi-pins.py outdated` compares each pin with its registry (git pins with the remote HEAD), and `python3 scripts/pi-pins.py bump [name ...]` rewrites npm pins to the latest release in `pins.py`, this README, and the tests; git pins move only when named. Review the diff, run the tests, then re-run the installer and reload pi.

`python3 scripts/pi-pins.py auto` keeps every npm pin on the latest release, major versions included, except `pi-herdr-agents`, whose bundled roles must be re-derived into `agents/` by hand. It runs only on a clean `main`, measures which test files already fail, then bumps all due pins, runs the remaining tests and `scripts/install.sh`, and starts pi once to confirm every package still loads. A pass becomes one commit; a failure restores the previous pins and reinstalls them, retries each pin on its own, and records the rejected version in `~/.local/state/weihung-agent-root/pi-autoupdate.json` so it is not tried again until a newer one appears. Git pins and `pi-herdr-agents` stay manual. `python3 scripts/pi-pins.py schedule` runs it daily at 06:00 through launchd (a Mac that is asleep then runs it on wake) and writes `~/.local/state/weihung-agent-root/pi-autoupdate.log`; `unschedule` removes it. The `PATH` recorded in the plist comes from the shell that ran `schedule`, so run it again after changing the Node version that provides `pi`.

| Package | Role |
|---|---|
| `pi-claude-bridge` | The `claude-bridge` provider: Claude models through the local Claude Code login. Pinned to the fork commit `wayne930242/pi-claude-bridge@b273512` on `weihung-integration`, rebuilt on upstream 0.9.1. It merges four upstream PRs still open upstream: 200K twins such as `claude-200k-opus-5-5` beside each 1M model ([#131](https://github.com/elidickinson/pi-claude-bridge/pull/131)), so a role can run Opus 5.5 at 200K while the main session runs 1M; `provider.reportApiCost`, which prices usage at API list prices ([#133](https://github.com/elidickinson/pi-claude-bridge/pull/133)); one-shot calls from extensions, such as `fetch_content`'s answer mode, served on an isolated Claude Code process instead of failing prompt capture ([#123](https://github.com/elidickinson/pi-claude-bridge/pull/123)); and tools an extension activates mid-turn, such as `web_enable` and `pi_lens_activate_tools`, reaching Claude in the same turn ([#125](https://github.com/elidickinson/pi-claude-bridge/pull/125)). Claude subscription usage comes from `pi-quotas`. |
| `pi-herdr-agents` | The `subagent` tool: dispatches workers into visible Herdr panes or isolated Git worktrees, with per-task model routing and a status widget. |
| `pi-mcp-adapter` | The `mcp` gateway for MCP servers. Servers come from `~/.config/mcp/mcp.json`, `~/.agents/mcp.json`, or pi's own config; host configs of other tools on the machine load as a lowest-precedence fallback because the installer sets `hostConfigDiscovery` to `on`. The installer registers `research-hub` (literature search, open-access download, and bibliography saves) launched through the pinned `npx thesis-toolkit`, with downloads in research-hub's default `~/downloads/papers`; a project `.mcp.json` entry of the same name takes precedence. It keeps `codebase-memory-mcp` disabled in case another tool's config still registers it, and turns off the per-server `mcp__<server>` proxy tools, so MCP servers are reached through `mcp` alone. These settings live in `~/.pi/agent/mcp-adapter.json`. pi-mcp-adapter 5.0.0 also reads pi's own `~/.pi/agent/mcp.json`, so servers added with `pi mcp add` work too; the installer leaves that file alone. It also adds `-builtin:mcp` to the settings `extensions`, because the adapter replaces pi's built-in MCP support, which would otherwise warn on every start. |
| `pi-intercom` | The `intercom` tool: messages and questions between pi sessions on the same machine. |
| `pi-ask-user` | The `ask_user` tool: structured questions with options for decisions that belong to the user. |
| `@juicesharp/rpiv-todo` | The `todo` tool and `/todos`: a task list with dependencies shown above the editor, rebuilt from the session so it survives `/reload` and compaction. |
| `pi-open-tui` | The interface: logo header, Starship-style footer with Git, context, and tokens, and a rounded editor. `/open-tui` edits its settings in `~/.pi/agent/open-tui.json`; the installer keeps the runtime, cost, and extension-status footer segments off. |
| `@sherif-fanous/pi-catppuccin` | The `catppuccin-mocha` theme, using only official Catppuccin Mocha palette colors to match Herdr, Ghostty, and SketchyBar. A package filter loads only `themes/catppuccin-mocha.json`. Install removes the earlier `@victor-software-house/pi-curated-themes`, whose `catppuccin-mocha` used off-palette accents. |
| `pi-web-access` | `web_search`, `fetch_content`, and video understanding, loaded on demand through `web_enable`. Search works without keys through Exa MCP or the Codex login; provider keys go in `~/.pi/agent/web-search.json`. |
| `pi-lens` | Diagnostics after each edit, `lens_diagnostics`, `read_symbol`, `read_enclosing`, and on-demand ast-grep and LSP navigation tools. The installer disables `project_report`, `symbol_search`, and `module_report` in `~/.pi-lens/config.json` to keep every prompt small; `read_symbol`, `read_enclosing`, and `lens_diagnostics` cover navigation and checks. |
| `pi-quotas` | Quota status in the footer and `/quotas` for every signed-in provider, plus per-provider commands such as `/anthropic:quotas` and `/codex:quotas`. `claude-bridge` reads the Claude Code login. Pinned to the fork commit `wayne930242/pi-quotas@caa30da` on `claude-bridge`, which adds `claude-bridge` support ([upstream PR #51](https://github.com/latentminds-ai/pi-quotas/pull/51)), until that PR is released. |
| `@moyai/pi-session-hoarder` | Verified local archives of every session in `~/.pi/agent/session-hoarder/`; `/hoarder status` reports it. Nothing leaves the machine unless `/hoarder storage s3` is configured. |
| `pi-jev-compaction` | Every compaction, including `idle-compaction`'s, first asks TypeSafe Jev which stale tool calls and results to drop or truncate and keeps user and assistant text verbatim; without `TYPESAFE_API_KEY` or on a Jev error it falls back to pi's summary. `/jev-status` shows the key and thresholds. |
| `cc-safety-net` | Blocks destructive commands (`git reset --hard`, `git push --force`, `rm -rf` on dangerous targets) and reads of secrets such as SSH keys, `.env`, and `~/.aws`, in every project. `npx cc-safety-net explain "<command>"` shows why a command is blocked; `npx cc-safety-net gui` edits the policy. |
| `pi-codex-image-gen` | The `codex_generate_image` tool: generates and edits images with the existing `openai-codex` login, so no `OPENAI_API_KEY` is needed. Its install telemetry stays off because the installer sets `enableInstallTelemetry` to `false`. |
| `pi-robot-hand` | The lazy kit. `robot_hand`: the agent hands the user a command, which lands in the prompt (shell commands as `! command`), the clipboard, or a new Herdr pane that closes and reports back when the command finishes; the agent never runs it. A `!command` typed while the agent is idle starts a turn on its output. `secret_drop`: the user types a secret into a masked dialog and applies it with a prefilled `!` command, so the value never enters the conversation; files it writes are then guarded from agent reads. |
| `@pify/memory` | Long-term memory as plain markdown: `memory_write`, `memory_read`, `memory_search` (SQLite FTS5 through `node:sqlite`, so Node 24+), `memory_forget`, and `memory_restore`, plus `/memory`. Global facts live in `~/.pi/agent/memory/` (`MEMORY.md` and `daily/`), project conventions in `.pi/memory/MEMORY.md`, injected only after the user consents. Recent failures and corrections return at the start of later sessions; every write passes a secret scan. Background session notes stay off until `/memory observe on`. Durable cross-project rules still belong in `rules/` and `pi/AGENTS.md.in`. |
| `pi-loop-monitor` | `/loop` for recurring, event, and idle wake-ups, and `MonitorCreate` to run a command in the background and wake the agent when it finishes, so waiting for CI or a deploy needs no `sleep`. State stays per session in `~/.pi/loops/`; `/monitors` lists loops and monitors. |
| `@narumitw/pi-goal` | `/goal <objective>` gives the session one objective and continues from Pi's idle boundary until the agent calls `goal_complete`, `goal_blocked`, or `goal_wait`; `/goal` opens a manager to pause, resume, edit, or clear it. Automatic turns stop after 25 responses or 3 no-progress runs unless `~/.pi/agent/pi-goal.json` changes the limits, and an optional token budget stops it sooner. Goal mode spends paid model turns unattended and edits the workspace. |
| `pi-phoenix-otel` | Streams every session to [Arize Phoenix](https://github.com/Arize-ai/phoenix) as OpenTelemetry traces: runs, turns with tokens and cost, and tool calls. It posts to `http://localhost:6006/v1/traces` unless `~/.pi/agent/phoenix-otel.config.json` says otherwise, `/otel-start` launches Phoenix through `uvx`, and exports fail silently while Phoenix is down. |
| `pi-code` | Claude Code's `.claude/rules` in every project: rules without `paths:` are inlined into the system prompt, and a rule with `paths:` globs is appended to the result of the first read, edit, or write that touches a matching file. A package filter loads only `extensions/claude-rules.ts`, because the package's other extensions duplicate the todo, MCP, subagent, and web packages above. Unscoped rules are delivered as context files, which `claude-bridge` forwards. |
| aaaav | The development workflow skills (`aaaav-do`, `investigating`, `inspecting`, `grilling`, and others) that the instructions route work through. |
| straw-boss | The Pi dispatch workflow: `boss-say`, `work-on`, `choosing-graph`, `shipping-task`, `reporting-to-user`, and `dispatching-work`, plus the `dispatch_control` tool (list, reattach, and hand off dispatches over `~/.pi/agent/dispatch-ledger/`) and Herdr pane balancing. Installed from `github.com/wayne930242/straw-boss` at the commit pinned in `scripts/pi-target.py`; bump the pin to take a new release. |

### This repository's pi package

[package.json](package.json) registers these extensions:

- [idle-compaction.ts](pi/extensions/idle-compaction.ts): compacts the session once it is idle with more than 300k tokens of context, so compaction never interrupts a running turn. The installer also sets pi's native threshold for the 1M `claude-bridge/claude-opus-5-5` to 500k (`compaction.modelOverrides` with `reserveTokens: 500000`), which only a long running turn reaches.
- [playwriter-relay.ts](pi/extensions/playwriter-relay.ts): at session start, starts the Playwriter relay on `127.0.0.1:19988` when it is down and warns when the Chrome extension is not connected, without delaying the session.

### Ported resources

- **mp-infra and sdlc** (only when their checkouts exist): installed as Pi packages, with mp-infra's hooks extension shipped in the plugin. Without a checkout the installer prints that it skipped the plugin, and a failing `pi install` for either one only warns.
- **team-toon-tack**: installed under `~/.local/share/weihung-agent-root/team-toon-tack`, providing the `managing-linear-tasks` skill, `/ttt-*` prompt templates, and the `ttt` CLI in `~/.local/bin`.

### Settings

| File | Keys |
|---|---|
| `~/.pi/agent/settings.json` | `packages`, `theme`, `editorPaddingX`, `collapseChangelog`, `enableInstallTelemetry` (`false`), `terminal.showTerminalProgress` |
| `~/.pi/agent/herdr-agents/config.json` | `models` (from [pi/herdr-agents-models.json](pi/herdr-agents-models.json)), `panes.mode` (`split`), `panes.direction` (`right`) |
| `~/.pi/agent/mcp-adapter.json` | `settings.hostConfigDiscovery`, `settings.namespaceProxyTools`, `mcpServers.codebase-memory-mcp.disabled`, `mcpServers.research-hub` |
| `~/.pi-lens/config.json` | `tools.project_report`, `tools.symbol_search`, and `tools.module_report` `.enabled` |

Other keys in these files stay as the user wrote them.

## Instructions and rules

`~/.pi/agent/AGENTS.md` is generated, not linked: edit [pi/AGENTS.md.in](pi/AGENTS.md.in) and re-run the installer. It covers language, work routing through skills, dispatch in Herdr, code discovery through LSP and ast-grep, and verification. It names the `pi-herdr-agents` roles but no model: models live in pi and `pi-herdr-agents` configuration.

The files in [rules/](rules/) (git safety, deployment, dependencies, clean architecture, UI design, skill writing, Chinese writing, and Go, Python, shell, TypeScript, and Markdown conventions) are not loaded into every session. The instructions list each file with the work it covers, and pi reads the matching file from `~/.pi/agent/rules/` before that work. A new rule file needs its entry in that list.

## Models

[pi/herdr-agents-models.json](pi/herdr-agents-models.json) is the `pi-herdr-agents` `models` object: `agents` sets each role's ordered model list, `default` a bare spawn's, and `tasks` the `task:<category>` candidates. The installer writes it into `~/.pi/agent/herdr-agents/config.json`; edit the repository file, run `bash scripts/install.sh`, and reload pi. An install stops when the home `models` changed since the last install, so a hand edit is never overwritten silently; move it into the repository file or rerun with `--force`. Thinking levels are set per dispatch, not in configuration.

pi's own default model and thinking level stay in `~/.pi/agent/settings.json` (`defaultProvider`, `defaultModel`, `defaultThinkingLevel`, `enabledModels`), managed by hand.

There is no model strategy profile or tier role any more; the installer removes the tier roles and marker keys an earlier install left behind.

## Phone access with Moshi (optional)

[Moshi](https://getmoshi.app) reaches pi sessions from a phone: it shows agent notifications and approvals, and attaches to the machine's terminal sessions over SSH or Mosh. The installer does not manage it.

```bash
brew install rjyo/moshi/moshi-hook
moshi-hook pair --token <pairing-token>   # token from the Moshi app
moshi-hook install --target pi            # writes ~/.pi/agent/extensions/moshi-hooks.ts
brew services start moshi-hook            # keeps the hook daemon running
```

For terminal access from outside the local network, join the machine and the phone to the same [Tailscale](https://tailscale.com) tailnet and pair the host with its tailnet address:

```bash
moshi-hook host enable-ssh
moshi-hook host setup --host <tailscale-hostname-or-100.x-address>
```

## Tests

```bash
bash tests/install.sh
bash tests/uninstall.sh
for test in tests/*.py; do python3 "$test"; done
for test in tests/*.mjs; do node --experimental-strip-types --test "$test"; done
```

The installer tests run against temporary homes with `--skip-external`; `tests/pi_fresh_machine.py` and `tests/pi_port_install.py` exercise the external install path with stub `npm`, `pi`, and `herdr` commands.

## 中文摘要

這個 repo 只管理 pi 的使用者層設定。新機器：clone 到 `~/projects/weihung-agent-root`，執行 `bash scripts/install.sh`，在 Herdr 裡啟動 `pi` 後以 `/login` 登入 OpenAI Codex；Claude 模型經由 pi-claude-bridge 使用本機 Claude Code 的登入。

- 安裝內容：pi 本體與 Herdr 整合、上表的 pi 套件（Herdr pane 派工、intercom、ask_user、todo、介面（pi-open-tui）與主題、MCP、網路搜尋、pi-lens、用量、session 備份、Jev 壓縮、危險指令防護（cc-safety-net）、Codex 畫圖（pi-codex-image-gen）、懶人工具（pi-robot-hand：指令交給使用者、`!` 指令自動回應、秘密輸入）、Phoenix 追蹤（pi-phoenix-otel）、Claude Code rules 載入（pi-code 的 claude-rules）、pi-skills，npm 套件皆鎖定版本）、aaaav、straw-boss（派工工作流、派工紀錄與復原、主代理移交、pane 平均分配）、Playwriter CLI（操作使用者自己的 Chrome，需另外安裝 Chrome 擴充套件）、本 repo 的擴充（閒置時自動壓縮、pi 啟動時確保 Playwriter 中繼服務在跑），公司 plugin mp-infra（含安全 hook）與 sdlc（有 checkout 時作為 Pi package，缺席或安裝失敗只警告），以及 team-toon-tack。
- 使用者規則在 `~/.pi/agent/rules/`，AGENTS.md 只列出每個檔案對應的工作，需要時才讀取。
- 模型：各 `pi-herdr-agents` 角色、預設與 task 的模型寫在 `pi/herdr-agents-models.json`，安裝程式會寫入 `~/.pi/agent/herdr-agents/config.json`；改模型請改 repo 的檔案再跑 `bash scripts/install.sh` 並重新載入 pi。pi 本身的預設模型在 `~/.pi/agent/settings.json`，手動維護。已不再有 model strategy profile 或 tier 角色；AGENTS.md 不列模型。
- 手機存取：可選用 Moshi（`moshi-hook`）搭配 Tailscale。
- 舊的 Claude Code、Codex、Gemini 多平台版本保存在 `legacy-claude-codex` tag。
