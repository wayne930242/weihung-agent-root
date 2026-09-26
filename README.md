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

Then start `pi` inside Herdr and run `/login` for OpenAI Codex. Claude models need no pi login; the bridge uses Claude Code's.

Clone beside the related checkouts when they exist: the installer uses `~/projects/aaaav` when present (otherwise `github.com/wayne930242/aaaav`) and the mp-infra plugin from `~/projects/moldplan-center` (or `PI_MP_INFRA_ROOT`).

Installer options:

- `--home PATH` installs into another home directory, for example a throwaway smoke test.
- `--skip-external` writes configuration only: no npm, pi package, Herdr, or network installs.
- `--force` backs up conflicting targets to `~/.local/state/weihung-agent-root/backups/<timestamp>/` before replacing them. Without it, a conflict stops the install.

A machine set up before the pi-only change still has the Claude Code, Codex, and Gemini links from that version. Remove them first with the legacy uninstaller: `git worktree add /tmp/legacy legacy-claude-codex && bash /tmp/legacy/scripts/uninstall.sh --target claude,codex,gemini`, then `git worktree remove /tmp/legacy`.

The installer is idempotent; re-run it after pulling changes. `bash scripts/uninstall.sh` (same `--home` and `--skip-external` options) removes this repository's links, packages, generated instructions, and settings, and restores what the install backed up. The pi binary, its logins, and `codebase-memory-mcp` stay.

## What the install sets up

`scripts/install.sh` links the repository into the home directory, installs `codebase-memory-mcp` into `~/.local/bin` when it is missing, and runs `scripts/pi-target.py install`, which:

- installs or upgrades pi (`npm install -g @earendil-works/pi-coding-agent`) and runs `herdr integration install pi`, which reports each pi session's state to Herdr;
- installs the pi packages below, aaaav, straw-boss, and this repository as a local pi package;
- generates `~/.pi/agent/AGENTS.md` from [pi/AGENTS.md.in](pi/AGENTS.md.in) plus the active model strategy;
- sets the default model, thinking level, `pi-herdr-agents` task models, UI settings, and MCP host-config discovery;
- ports resources pi cannot install as packages: codebase-memory, mp-infra, and team-toon-tack.

Every file it writes is recorded in `~/.pi/agent/.weihung-agent-root.json`, so uninstall removes exactly those files and restores the previous settings values.

### Links

| Home path | Source |
|---|---|
| `~/.agents/skills/<name>` | [skills/](skills/): `managing-model-preferences`, `providing-knowledge`, `reflecting-to-root`, `writing-great-skills` |
| `~/.pi/agent/rules` | [rules/](rules/): user-global rules |
| `~/.pi/agent/agents` | [agents/](agents/): global overrides of the `pi-herdr-agents` 2.0.4 bundled roles. Each file is the bundled role with its `tools:` allowlist removed, so a child loads every installed tool; the bundled `spawning:` policy still limits nested subagents. Re-derive them when the `pi-herdr-agents` pin changes. |
| `~/.pi/agent/skills/pi-skills` | A clone of [badlogic/pi-skills](https://github.com/badlogic/pi-skills) in `~/.local/share/weihung-agent-root/pi-skills`, pulled on each install. Its skills (`brave-search`, `browser-tools`, `gccli`, `gdcli`, `gmcli`, `transcribe`, `vscode`, `youtube-transcript`) need their own CLIs or keys as each `SKILL.md` describes. |

### Packages

Registry packages are pinned to exact versions in [scripts/pi-target.py](scripts/pi-target.py), so every machine installs the same release and `pi update` leaves them alone; bump a version there and re-run the installer.

| Package | Role |
|---|---|
| `pi-claude-bridge` | The `claude-bridge` provider: Claude models through the local Claude Code login. Pinned to the fork commit `wayne930242/pi-claude-bridge@2f00cce` on `weihung-integration`, which merges five upstream PRs: 200K twins such as `claude-200k-opus-5-5` beside each 1M model ([#131](https://github.com/elidickinson/pi-claude-bridge/pull/131)), so main and complex tiers run Opus 5.5 1M while other tiers run 200K; Claude subscription usage in the footer plus `/claude-usage` ([#132](https://github.com/elidickinson/pi-claude-bridge/pull/132)); `provider.reportApiCost`, which prices usage at API list prices ([#133](https://github.com/elidickinson/pi-claude-bridge/pull/133)); one-shot calls from extensions, such as `fetch_content`'s answer mode, served on an isolated Claude Code process instead of failing prompt capture ([#123](https://github.com/elidickinson/pi-claude-bridge/pull/123)); and tools an extension activates mid-turn, such as `web_enable` and `pi_lens_activate_tools`, reaching Claude in the same turn ([#125](https://github.com/elidickinson/pi-claude-bridge/pull/125)). |
| `pi-herdr-agents` | The `subagent` tool: dispatches workers into visible Herdr panes or isolated Git worktrees, with per-task model routing and a status widget. |
| `pi-mcp-adapter` | The `mcp` gateway for MCP servers. Servers come from `~/.config/mcp/mcp.json`, `~/.agents/mcp.json`, or pi's own config; host configs of other tools on the machine load as a lowest-precedence fallback because the installer sets `hostConfigDiscovery` to `on`. The installer disables the imported `codebase-memory-mcp`, whose tools `cbmem.ts` already registers directly, and turns off the per-server `mcp__<server>` proxy tools, so MCP servers are reached through `mcp` alone. |
| `pi-intercom` | The `intercom` tool: messages and questions between pi sessions on the same machine. |
| `pi-ask-user` | The `ask_user` tool: structured questions with options for decisions that belong to the user. |
| `@juicesharp/rpiv-todo` | The `todo` tool and `/todos`: a task list with dependencies shown above the editor, rebuilt from the session so it survives `/reload` and compaction. |
| `pi-open-tui` | The interface: logo header, Starship-style footer with Git, context, tokens, and cost, and a rounded editor. `/open-tui` edits its settings in `~/.pi/agent/open-tui.json`. |
| `@victor-software-house/pi-curated-themes` | The `catppuccin-mocha` theme, matching Herdr's `catppuccin` theme. A package filter loads only `themes/catppuccin-mocha.json` and none of the package's skills. |
| `pi-web-access` | `web_search`, `fetch_content`, and video understanding, loaded on demand through `web_enable`. Search works without keys through Exa MCP or the Codex login; provider keys go in `~/.pi/agent/web-search.json`. Pinned to the fork commit `wayne930242/pi-web-access@3b13c02`, which reads Pi's exported `VERSION` so lazy activation works under a global Pi install ([upstream PR #429](https://github.com/nicobailon/pi-web-access/pull/429)). |
| `pi-lens` | Diagnostics after each edit, `lens_diagnostics`, `read_symbol`, `read_enclosing`, and on-demand ast-grep and LSP navigation tools. The installer disables `project_report`, `symbol_search`, and `module_report` in `~/.pi-lens/config.json`, because codebase-memory owns structural discovery. |
| `pi-usage` | The `/usage` command: daily and weekly limits of the current provider. Pinned to the fork commit `wayne930242/pi-usage@a683c24`, which adds `claude-bridge` by reading Claude Code's login ([upstream PR #4](https://github.com/iefnaf/pi-usage/pull/4)); Codex, Z.AI, and Kimi work as in the npm release. |
| `@moyai/pi-session-hoarder` | Verified local archives of every session in `~/.pi/agent/session-hoarder/`; `/hoarder status` reports it. Nothing leaves the machine unless `/hoarder storage s3` is configured. |
| `pi-jev-compaction` | Every compaction, including `idle-compaction`'s, first asks TypeSafe Jev which stale tool calls and results to drop or truncate and keeps user and assistant text verbatim; without `TYPESAFE_API_KEY` or on a Jev error it falls back to pi's summary. `/jev-status` shows the key and thresholds. |
| `cc-safety-net` | Blocks destructive commands (`git reset --hard`, `git push --force`, `rm -rf` on dangerous targets) and reads of secrets such as SSH keys, `.env`, and `~/.aws`, in every project. `npx cc-safety-net explain "<command>"` shows why a command is blocked; `npx cc-safety-net gui` edits the policy. |
| `pi-codex-image-gen` | The `codex_generate_image` tool: generates and edits images with the existing `openai-codex` login, so no `OPENAI_API_KEY` is needed. Its install telemetry stays off because the installer sets `enableInstallTelemetry` to `false`. |
| aaaav | The development workflow skills (`aaaav-do`, `investigating`, `inspecting`, `grilling`, and others) that the instructions route work through. |
| straw-boss | The Pi dispatch workflow: `boss-say`, `work-on`, `choosing-graph`, `shipping-task`, `reporting-to-user`, and `dispatching-work`, plus the `dispatch_control` tool (list, reattach, and hand off dispatches over `~/.pi/agent/dispatch-ledger/`) and Herdr pane balancing. Installed from `github.com/wayne930242/straw-boss` at the commit pinned in `scripts/pi-target.py`; bump the pin to take a new release. |

### This repository's pi package

[package.json](package.json) registers these extensions:

- [idle-compaction.ts](pi/extensions/idle-compaction.ts): compacts the session once it is idle with more than 300k tokens of context, so compaction never interrupts a running turn.
- [mp-infra-hooks.ts](pi/extensions/mp-infra-hooks.ts): when `~/.pi/agent/mp-infra.json` exists, runs the mp-infra session-start hook, its production-safety check before shell commands, and its vault, playbook, and Nomad checks after edits.

### Ported resources

- **codebase-memory**: the official `codebase-memory-mcp install --clients=pi` output, generated in a staging home and installed as `~/.pi/agent/extensions/cbmem.ts` and the `codebase-memory` skill, pointing at `~/.local/bin/codebase-memory-mcp`.
- **mp-infra** (only when its checkout exists): its skills linked into `~/.pi/agent/skills/`, and `~/.pi/agent/mp-infra.json` for the hooks extension. Without the checkout the installer prints that it skipped mp-infra.
- **team-toon-tack**: installed under `~/.local/share/weihung-agent-root/team-toon-tack`, providing the `managing-linear-tasks` skill, `/ttt-*` prompt templates, and the `ttt` CLI in `~/.local/bin`.

### Settings

| File | Keys |
|---|---|
| `~/.pi/agent/settings.json` | `packages`, `defaultProvider`, `defaultModel`, `defaultThinkingLevel`, `enabledModels` (every model the active strategy's tiers use), `theme`, `editorPaddingX`, `collapseChangelog`, `enableInstallTelemetry` (`false`), `terminal.showTerminalProgress` |
| `~/.pi/agent/herdr-agents/config.json` | `models.default`, `models.tasks`, `status`, `panes.mode` (`split`), `panes.direction` (`right`) |
| `~/.pi/agent/mcp.json` | `settings.hostConfigDiscovery`, `settings.namespaceProxyTools`, `mcpServers.codebase-memory-mcp.disabled` |
| `~/.pi-lens/config.json` | `tools.project_report`, `tools.symbol_search`, and `tools.module_report` `.enabled` |

Other keys in these files stay as the user wrote them.

## Instructions and rules

`~/.pi/agent/AGENTS.md` is generated, not linked: edit [pi/AGENTS.md.in](pi/AGENTS.md.in) and re-run the installer. It covers language, work routing through skills, dispatch in Herdr, code discovery with codebase-memory, and verification, and ends with the active strategy's model tiers.

The files in [rules/](rules/) (git safety, deployment, dependencies, clean architecture, UI design, skill writing, Chinese writing, and Go, Python, shell, TypeScript, and Markdown conventions) are not loaded into every session. The instructions list each file with the work it covers, and pi reads the matching file from `~/.pi/agent/rules/` before that work. A new rule file needs its entry in that list.

## Model strategies

[skills/managing-model-preferences](skills/managing-model-preferences/) keeps a catalog of named strategies. [model-preference-profile.md](skills/managing-model-preferences/model-preference-profile.md) names the active one and holds the tier guide: which kind of work goes to `main`, `docs`, `recon`, `ui`, `review`, `simple`, `coding`, `complex_clear`, `complex_unclear`, or `academic`. [pi/model-profiles.json](pi/model-profiles.json) holds each strategy's exact `provider/model-id` and thinking level per tier, and each `strategies/<name>.md` mirrors its table with the rationale.

`scripts/pi-target.py` turns the active strategy into pi configuration:

- the `main` tier becomes pi's default model and thinking level;
- every tier becomes a line in `~/.pi/agent/AGENTS.md` with an ordered model list, so a dispatch passes the tier's models and thinking level explicitly;
- `pi-herdr-agents` task categories get the same candidates: `coding`, `review`, `recon`, and `docs` from their tiers, `qa` from `review`, and `architecture` from `complex_unclear`.

Each list pairs the tier's model with a fallback from the other provider: a `claude-bridge` tier falls back to the matching OpenAI Codex model; a Luna tier falls back to `claude-bridge/claude-haiku-4-5`, and any other `openai-codex` tier to `claude-bridge/claude-opus-5-5` (1M) for main and complex tiers or `claude-bridge/claude-200k-opus-5-5` otherwise.

To switch, run `/managing-model-preferences <strategy>` in pi, or change the active link yourself and run:

```bash
python3 scripts/pi-target.py apply-profile --home "$HOME"
```

then reload pi.

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

- 安裝內容：pi 本體與 Herdr 整合、上表的 pi 套件（Herdr pane 派工、intercom、ask_user、todo、介面（pi-open-tui）與主題、MCP、網路搜尋、pi-lens、用量、session 備份、Jev 壓縮、危險指令防護（cc-safety-net）、Codex 畫圖（pi-codex-image-gen）、pi-skills，npm 套件皆鎖定版本）、aaaav、straw-boss（派工工作流、派工紀錄與復原、主代理移交、pane 平均分配）、本 repo 的擴充（閒置時自動壓縮、mp-infra 安全 hook），以及 codebase-memory、mp-infra（有 checkout 時）與 team-toon-tack。
- 使用者規則在 `~/.pi/agent/rules/`，AGENTS.md 只列出每個檔案對應的工作，需要時才讀取。
- 模型策略：profile 指定啟用策略，`pi/model-profiles.json` 定義各 tier 的模型與 thinking，`apply-profile` 會更新 pi 預設模型、派工候選與 AGENTS.md。
- 手機存取：可選用 Moshi（`moshi-hook`）搭配 Tailscale。
- 舊的 Claude Code、Codex、Gemini 多平台版本保存在 `legacy-claude-codex` tag。
