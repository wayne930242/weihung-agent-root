# weihung-user-claude

Personal user-root light agent system for Claude Code, Codex, and Antigravity.

The repo keeps global behavior in version control, but deliberately separates:

- shared working agreements
- Claude-specific prompt, agents, and hooks
- Codex-specific prompt, subagents, rules, and hooks
- Antigravity-specific rules and global customizations

The goal is to keep the user-root layer thin and stable, while leaving personal machine config such as credentials, MCP servers, and trusted project state under direct user control.

## Design

This repo follows a light split:

- `shared/`: cross-product principles that are stable across tools
- `claude/`: assets that only make sense for Claude Code
- `codex/`: assets that only make sense for Codex

That split matters because the products do not expose the same primitives:

- Claude uses `CLAUDE.md`, `~/.claude/settings.json`, and Markdown subagents
- Codex uses `AGENTS.md`, `rules/*.rules`, `hooks.json`, and TOML subagents

Trying to force both products through one identical file model creates unnecessary coupling.

For the longer design boundary, including what this repo should borrow from larger toolkits such as ECC and what it should avoid, see [docs/design-principles.md](docs/design-principles.md).

## Layout

```text
CLAUDE.md                          # thin Claude root prompt, imports shared fragments
AGENTS.md                          # thin Codex root prompt
shared/
  communication.md
  engineering.md
  context-management.md
claude/
  agents/
    security-reviewer.md
    silent-failure-hunter.md
  hooks/
    log-notification.sh
    log-stop.sh
    sync-repo.sh
    warn-unpushed.sh
  statusline.sh
codex/
  agents/
    article-writer.toml
    docs-researcher.toml
    security-reviewer.toml
    silent-failure-hunter.toml
  rules/
    weihung.rules                  # managed policy; default.rules stays Codex-owned
  hooks/
    log-session-start.sh
    log-stop.sh
  hooks.json
rules/
  clean-architecture.md
  go.md
  typescript.md
  python.md
  shell.md
  markdown.md
  deployment.md
  chinese-writing.md
  dependencies.md
  git-safety.md
  skill-writing.md
  memory-index-sync.md
  ui-design.md
skills/
  managing-model-preferences/      # also the /managing-model-preferences command
  providing-knowledge/
  reflecting-to-root/
  writing-great-skills/
evals/
  mini-spec-3r.sh                  # real agent-behavior eval, run on demand
scripts/
  install.sh
  uninstall.sh
  bootstrap.sh
  bridge-claude-projects.sh
  install-codex-desktop-wsl.sh
  token-sinks.py                   # where Claude Code token spend goes
config/
  claude-hooks.json
  claude-settings.json             # Opus 1M main, 300k auto-compact, cross-session, empty commit/PR attribution
  codex-managed.toml               # 300k auto-compact and [tui] status line, merged into ~/.codex/config.toml
  gemini-skills.json               # registers .claude/skills for Antigravity
```

## AAAAV Development Loop (Mini SDD)

The durable and inline development workflow is provided by `aaaav-do` from the [aaaav](https://github.com/wayne930242/aaaav) plugin, which installs itself: Align → Advance → Anchor → Act → Verify.
In Chinese: 對齊 → 推進/延續 → 定錨 → 實作 → 驗證. Advance carries Decision → Spec →
Design without changing owner or restarting context after the agent enters the
target project.

Five rules carry it, and nothing else is enforced:

- **Align and route.** Every source change restates the task and intended outcome
  in the model's own words and declares itself Inline or Durable. Clear,
  localized, low-reuse work stays inline and writes no files; ambiguity,
  cross-module or cross-session scope, a lasting contract, high risk, scope
  expansion, or a user who wants the spec first makes it durable and leaves
  `decision.md`, `spec.md`, `design.md`, and `verification.md` under
  `docs/specs/YYYY-MM-DD-<slug>/`. Existing folders keep `requirements.md` as
  their decision artifact.
- **Advance decisions.** New durable work writes exploratory questions, answers,
  bases, and statuses to `decision.md`. Grounded answers advance directly;
  `grill-with-docs` asks only the unresolved user-owned frontier. The same run
  then prepares the spec and design.
- **Ratify.** Inline work states one observable `Contract:` and records the
  user's request as its `Authorization:`, then executes without re-asking.
  Durable work sits at `Status: proposed` — which forbids production edits —
  until the user's explicit reply sets `Status: approved`, `Approved at`, and
  `Approved from`.
- **Anchor and act.** Before the first production edit, choose the simplest
  credible reality anchor and checkpoint, then implement through the target
  project's native practices.
- **Result.** Verification gives every requirement its own
  `Requirement | Evidence | Result` row, with `pass`, `fail`, or `unknown`. A
  green suite is not evidence for a requirement nothing exercised.

No hook enforces any of this. The contract is the text the agent reads, and
[`evals/mini-spec-3r.sh`](evals/mini-spec-3r.sh) proves a real agent follows it.

Phase transitions, the artifact contract (`MINI-SDD.md`), and the debug loop
(`DEBUGGING.md`) live in the aaaav plugin's `aaaav-do` skill.

## Install

Install into your real user root:

```bash
bash scripts/install.sh
```

Bootstrap a new machine by cloning or updating the repo into the standard location and then running the installer:

```bash
bash scripts/bootstrap.sh
```

Install the repository-managed Codex agent system into Windows Codex Desktop
from WSL:

```bash
bash scripts/install-codex-desktop-wsl.sh
```

The Desktop installer discovers the Windows user profile automatically and
copies only the managed Codex surface. It preserves Windows-only `.system`
skills, plugins, `config.toml`, authentication, history, and runtime state.
Conflicting managed targets fail safely; use `--force` to back them up under
Windows Local AppData before replacement:

```bash
bash scripts/install-codex-desktop-wsl.sh --force
```

Remote one-liner bootstrap:

```bash
curl -fsSL https://raw.githubusercontent.com/wayne930242/weihung-user-claude/main/scripts/bootstrap.sh | bash
```

Smoke test against a fake home first:

```bash
bash scripts/install.sh --home /tmp/weihung-user-claude-smoke
```

Replace conflicting managed targets only when you mean it:

```bash
bash scripts/install.sh --force
```

Forward installer flags through bootstrap the same way:

```bash
bash scripts/bootstrap.sh --force
```

Uninstall managed assets and restore from the latest backup when available:

```bash
bash scripts/uninstall.sh
```

## Managed Surface

The installer manages only these user-root surfaces.

### Claude

- `~/.claude/CLAUDE.md`
- `~/.claude/shared/*.md`
- `~/.claude/skills/*/`
- `~/.claude/agents/*.md`
- `~/.claude/rules/*.md`
- `~/.claude/hooks/*.sh`
- `~/.claude/statusline.sh`
- merge into `~/.claude/settings.json` using `config/claude-hooks.json` (hooks + `statusLine` block)
- merge into `~/.claude/settings.json` using `config/claude-settings.json` (model, auto-compact window, `env`, cross-session settings, empty commit/PR attribution)
- drop any `~/.claude/hooks/*` registration whose script no longer exists, so a hook this repo
  used to manage cannot survive its own removal and fail every event with exit 127

### Codex

- `~/.codex/AGENTS.md`
- the keys of `config/codex-managed.toml` (top-level, `[tui]` status line, and explicitly disabled plugins) inside `~/.codex/config.toml`; every other line stays as written
- `~/.agents/skills/*/` (Codex's personal skill location)
- `~/.codex/agents/*.toml`
- `~/.codex/rules/weihung.rules`; Codex keeps writing session approvals to its own `~/.codex/rules/default.rules`
- `~/.codex/hooks/*.sh`
- `~/.codex/hooks.json`

### Antigravity

- `~/.gemini/config/AGENTS.md`
- `~/.gemini/config/GEMINI.md`
- `~/.gemini/config/skills.json`
- `~/.gemini/config/skills/*/`
- `~/.gemini/config/rules/*.md`

## Bridging Existing Claude Projects to Antigravity

To use Antigravity with your existing Claude Code projects without manual migration:

1. **Global Skills Auto-Discovery**: `~/.gemini/config/skills.json` automatically registers `.claude/skills` for any open workspace.
2. **Batch Project Bridge**: Run `bash scripts/bridge-claude-projects.sh [DIR...]` (defaults to current directory) to scan projects and establish relative symlinks:
   - `AGENTS.md -> CLAUDE.md`
   - `.agents/skills -> ../.claude/skills`

## Intentionally Not Managed

These remain user-controlled on purpose:

- `~/.claude/settings.local.json`
- `~/.codex/config.toml`, apart from the keys in `config/codex-managed.toml`
- `~/.gemini/config/config.json`
- `~/.gemini/config/mcp_config.json`
- `~/.gemini/settings.json`
- `~/.gemini/antigravity-cli/settings.json`
- shell startup files such as `~/.zshenv`
- credentials and auth
- MCP server definitions
- plugin enablement, except the plugins explicitly disabled by `config/codex-managed.toml`
- trust and approval state

Plugin enablement stays yours apart from the explicit disabled list in `config/codex-managed.toml`. The installer also prints the Codex plugin install commands when `enabledPlugins` does not already carry `codex@openai-codex`, because the cross-model routing in `CLAUDE.md` has nothing to route to without it.

This is especially important for Codex. `config.toml` often carries machine-local trust, MCP, plugin, and feature flags that should not be overwritten by a global prompt repo.

派工模型由 [模型偏好 profile](skills/managing-model-preferences/model-preference-profile.md)
集中管理。Claude 與 Codex 的根提示在 `boss-say` 派工前讀取它，明確傳入模型與 effort。
每期調整可使用 `managing-model-preferences` skill，例如：「更新本期模型偏好，一般工作改用指定模型」。
profile、具名策略與 skill 透過現有安裝腳本一起連結到兩個平台。
目前最佳策略為 `claude-only`：例行派工全部留在 Claude，Opus 5.5 high 協調，Opus 5.5 low 承接明確小修改與查找整理，Opus 5.5 medium 一般實作與文件，Opus 5.5 1M low 承接 UI/UX 審查與指示清楚的複雜工作，Opus 5.5 1M xhigh 承接指示不清的複雜工作。
既有策略保存為 `claude-drive-codex`、`codex-drive-claude`、`codex-first` 與 `claude-coding-codex-doc`。
每套策略獨立存檔並以 Git 追蹤修訂，切換時更新 profile 的啟用連結。
查看目前策略、切換策略或新增策略都可使用 `/managing-model-preferences` 指令，例如 `/managing-model-preferences`（查看）或 `/managing-model-preferences claude-drive-codex`（切換）。

簡單工作可沿用直接完成的流程；主代理權限移交由 Straw Boss 的
`handoff-orchestrator` 處理。主會話的 Opus 1M 設定及原生專用角色 TOML
各自維持原用途；套用 profile 的派工明確指定其選定的模型與 effort。

On upgrade, the installer removes the former repository-managed
`env.CLAUDE_CODE_SUBAGENT_MODEL=sonnet` and `advisorModel=opus` values. It
preserves another worker-model or advisor value and every unrelated environment
setting before installing the Opus 1M main model.

## Conflict And Backup Behavior

- Default behavior is fail-fast. If a managed target already exists, installation stops.
- `--force` moves conflicting files into `~/.local/state/weihung-user-claude/backups/<timestamp>/` before replacing them.
- Claude `settings.json` is merged, not symlinked, so existing non-hook settings remain intact.
- Codex `config.toml` keeps every line except the keys in `config/codex-managed.toml`.

## Uninstall Behavior

- `scripts/uninstall.sh` looks for the latest backup under `~/.local/state/weihung-user-claude/backups/`.
- If a backup exists for a managed path, that file is restored.
- If no backup exists for a managed path, the managed symlink is removed.
- Every `~/.claude/settings.json` entry pointing at a `claude/hooks/*.sh` script is removed, not
  only the entries that still match `config/claude-hooks.json`, so an older release's
  registration cannot outlive the script it names.
- The managed `model` is removed only while it still holds the installed value;
  user-edited model and advisor values survive.
- Managed keys in `~/.codex/config.toml` are removed only while they still hold the installed value.
- `~/.gemini/config/config.json` is left untouched, because it is not installer-managed.

## Claude Notes

Claude supports user memory and imports, so the Claude side is intentionally thin:

- `CLAUDE.md` holds routing and Claude-only behavior
- `@shared/...` imports pull in stable cross-product guidance
- hooks are wired through `settings.json`, because that is Claude's official hook surface

Current Claude hooks are deliberately minimal:

- `Stop` logs to `~/.claude/state/weihung-user-claude/hooks.jsonl`

The statusline (`claude/statusline.sh`) is also managed.
Color and a `⚠` icon scale to the model's compact-recommendation threshold.
1M-context models warn at 30% (≈300K tokens); 200K models warn at 70% (≈140K tokens).
Detection keys off `display_name` containing `1M`/`1m`.

![Claude Code statusline](docs/images/statusline.png)

## Codex Notes

Codex now has first-class support for:

- global and project `AGENTS.md`
- `rules/*.rules`
- `hooks.json`
- custom subagents in `agents/*.toml`

This repo uses that split directly:

- `AGENTS.md` stays focused on general working agreements
- `codex/rules/weihung.rules` handles approval policy
- `codex/hooks.json` and `codex/hooks/*.sh` handle automation
- `codex/agents/*.toml` handle specialized delegation

Hooks and multi-agent tools are stable and on by default, so no feature flag is needed.
Agent role files apply only `developer_instructions`, model, reasoning, and a few
related overrides; sandbox and MCP settings always come from the parent session.

### Migration

Earlier releases linked skills into `~/.codex/skills`, installed Claude commands into
`~/.claude/commands`, and linked `~/.codex/rules/default.rules` to this repo.
The installer prunes those repository links, and moves directory copies of repository
skills found in `~/.agents/skills` to the backup before linking the current versions.

## Experimental Jev Context Pruning

Compaction for both harnesses is configured here: `config/claude-settings.json` sets
`autoCompactWindow` to 300000, and that compaction event is what Jev pruning hooks.
The pruning runtime itself is vendored in the [straw-boss](https://github.com/weihung/straw-boss)
plugin; this repo owns the wiring that decides whether it can run at all.

Jev prunes tool records VERBATIM instead of summarizing: each tool call and its result
is scored, then kept, truncated, or dropped, while user and assistant text is always
kept word for word. Governing sources -- dispatch contracts, `AGENTS.md`, `CLAUDE.md`,
`GEMINI.md` and `SKILL.md` reads -- are kept by rule, never by score. Dropped content is
stored so a wrong deletion stays recoverable.

`CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1` is installed through `config/claude-settings.json`,
which only allows plugin function hooks to load. It does not turn pruning on.

### Shell environment

Two exports belong in `~/.zshenv`. The installer never writes shell startup files, so
add them by hand:

```sh
export TYPESAFE_API_KEY="<your TypeSafe key>"
export CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1
```

`TYPESAFE_API_KEY` is what Jev authenticates with. `CLAUDE_CODE_ENABLE_FUNCTION_HOOKS=1`
is also installed into `~/.claude/settings.json` from `config/claude-settings.json`; the
export carries the same flag to tooling launched from a shell rather than from that file.

`STRAW_BOSS_JEV` stays out of `~/.zshenv` and out of global settings on purpose. Putting
it there turns pruning on for every session at once, which is exactly what the renewal
acceptance window below rules out.

### Turning it on and off

Pruning is off unless a session explicitly asks for it, and it needs `TYPESAFE_API_KEY`
in the environment. Enable it for one newly launched Claude session:

```sh
STRAW_BOSS_JEV=1 claude
```

Start a session with the experiment explicitly off:

```sh
STRAW_BOSS_JEV=0 claude
```

An unset or empty `TYPESAFE_API_KEY` skips the path silently: no error, no benchmark
record, and ordinary compaction behavior.

### Codex

Codex 0.155.1 exposes no replacement-history interface through its public `PreCompact`
or `thread/compact/start`, so live pruning cannot run there. Codex shares the criteria,
policy, gate and benchmark contract, and its pruning runs as an opt-in copy adapter
rather than in a live session. Runtime parity with Claude is not currently achievable.

### While the renewal acceptance window is open

Keep pruning off for ordinary sessions through 2026-09-25. The context renewal
seven-day acceptance measures token sinks against a baseline, and pruning every daily
compaction makes that comparison unreadable.

This is why `STRAW_BOSS_JEV` is set per session rather than exported from `~/.zshenv`.
After 2026-09-25 the switch can move into the shell environment if the benchmark records
justify it.

## Why This Is Light

- The global prompt files are short.
- Every source-changing route uses the embedded Mini SDD lifecycle; low-reuse
  local work stays inline and durable work leaves phased artifacts under
  `docs/specs/`.
- Approval policy is not mixed into prompt prose.
- Automation is not mixed into prompt prose.
- Product-specific capabilities live in product-specific directories.
- The installer does not silently take over the full home config surface.

## Verification

The repo currently verifies:

- installer behavior with `tests/install.sh`
- Windows Codex Desktop installer behavior with `tests/install_codex_desktop_wsl.sh`
- Claude hook scripts with `tests/hooks.sh`
- Codex hook scripts with `tests/codex_hooks.sh`
- bootstrap clone/update behavior with `tests/bootstrap.sh`
- uninstall restore/remove behavior with `tests/uninstall.sh`
- prompt routing rules and Mini Spec deletion guards with `tests/prompts.sh`
- token spend accounting with `tests/token_sinks.sh`
- Codex plugin cache version keeper with `tests/codex_plugin_cache_keeper.sh`

`tests/` proves the rules are still written down. Whether an agent obeys them is
a separate question, answered by `evals/mini-spec-3r.sh`: it installs this repo
into a throwaway home, drives a headless agent against a throwaway project, and
asserts what changed on disk — inline work executing directly, durable work
stopping before any source edit, and approved durable work producing
per-requirement evidence. It costs money and is not deterministic, so it runs on
demand rather than with the test suite.

```bash
bash evals/mini-spec-3r.sh
```

Whether the agent system spends tokens well is a third question.
`scripts/token-sinks.py` reads local Claude Code transcripts and reports cost composition, cost by context size, single-tool round-trips, subagent share, fixed prefix size, and the most expensive projects and sessions.
Run the same length of window before and after a change to the agent system and compare the two reports.
Claude Code deletes transcripts after 30 days by default, so save the before report outside this public repository.

```bash
python3 scripts/token-sinks.py --since 2026-09-03 --until 2026-09-18 \
  > ~/.claude/state/weihung-user-claude/token-sinks/baseline-2026-09-03_2026-09-18.txt
```

## Not Tracked

- personal values in `settings.json` / `settings.local.json`
- generated state such as `todos/`, `projects/`, `statsig/`
- machine-specific additions outside the managed surfaces above
