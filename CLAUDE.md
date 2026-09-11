Never use Simplified Chinese. Always use Traditional Chinese for all communication.
All prompts and agent instructions must be in English.

提示詞、文件與文章應直接陳述期望行為，避免不必要的防禦性用語。

Be concise and answer what was asked.
Source-changing work invokes `leveraging-tasks` and states its Alignment and Reality anchor before the first production edit.
Resolve uncertainty from the conversation context before asking the user.

@shared/communication.md
@shared/engineering.md
@shared/context-management.md

# Delegated Operational Authority

IMPORTANT: The "ask when uncertain" / "present, don't pick silently" defaults in `shared/communication.md` and `shared/engineering.md` are about genuine ambiguity — an architecture choice, an unclear scope, a judgment call that's actually mine to make. They do not apply to a decision a skill or role you're operating under has already delegated to you — e.g. an orchestrator/main-agent role instructed to decide and state a dispatch or coordination call, not ask. Follow that skill's own delegation there: state the decision and act, don't re-ask me.

# Routing

IMPORTANT: Before responding to a significant request, choose one owner:

- A named or exact specialized skill → use it.
- Explanation or comparison → `providing-knowledge`.
- Research → `investigating`.
- Check, audit, or review → `inspecting`.
- Human feedback on working output → `human-feedback`.
- Any source-changing work → `leveraging-tasks`.
- A user-owned unresolved decision → `grilling`.

Source-changing work that needs a managed app's own working directory routes
through `boss-say` instead, and `leveraging-tasks` then runs inside the
dispatched session rather than here. See Complex Delegation below.

A specialized skill hands what it established to the implementation owner, which
continues from there — the finding travels, the work does not restart.

# Model Work Routing

模型偏好以 `~/.claude/skills/managing-model-preferences/model-preference-profile.md` 為準；在本專案內使用 `skills/managing-model-preferences/model-preference-profile.md`。進入 `boss-say` 或選擇委派模型前讀取，調整偏好使用 `managing-model-preferences` skill。

Carry simple work from a direct user instruction yourself.
Delegate other fragmentary tasks through Straw Boss or a subagent.
Use Straw Boss when the task needs a managed app workroom, its real harness,
durable coordination, or source-changing work in that app.
Use a subagent for a self-contained fragment that does not need the managed
app's own workroom.

依 profile 的順序選擇 agent kind、model 與 effort，明確帶入派工參數。

When Straw Boss itself causes friction, repair it in
`~/projects/straw-boss`, bump and push the plugin, run
`bash scripts/install.sh` in that checkout, then resume the original work.

# Orchestrator 權限移交

需要移交主代理權限時，依 Straw Boss 的 `handoff-orchestrator` 與 `docs/roles.md` 辦理；接手模型依當期 profile 與使用者的明確指定選擇。

# Complex Delegation

A delegation is complex when it needs the target app's real harness or worktree, spans multiple steps or components, or benefits from mid-flight coordination.
Route every complex delegation through the Straw Boss plugin's `boss-say` skill.
Require `dispatching-work` to use a live `herdr-pane` so the user can watch, join, and answer the dispatched agent directly.
If Herdr is unavailable, report that the in-loop route is blocked before changing transport; do not silently replace it with a plain subagent, direct `/codex:rescue`, or a headless dispatch.

<!-- straw-boss:agent-routing:start -->
# UI/UX Design Codex Refinement

Dispatch a final review-and-refinement pass to `codex` through Straw Boss and Herdr only when the completed work introduces new UI/UX design, needs design judgment, or sets a new design direction.
User-facing surfaces include web, desktop, mobile, browser extensions, terminal/TUI workflows, and other interfaces people directly operate.

Do not dispatch this pass when the work only applies an existing layout, design system, or component pattern, or when the frontend requirement is already specified and only needs implementation to that spec.
General frontend work is not a trigger by itself; the normal verification for that work is enough.

依 model-preference-profile.md 明確指定模型與 effort，讓設計與審查工作取得當期選定的組合。

When it does trigger, Codex must operate the closest available real interface, inspect the result, make any source or configuration adjustments needed within the original request, and repeat the real-interface check until no actionable finding remains.
It may make those scoped adjustments without asking for approval at each iteration; return after the pass with the changes, evidence, and any remaining blocker.

This refinement authority does not expand product scope or authorize destructive or external actions, commit, push, merge, deployment, release, submission, or authentication bypass.
<!-- straw-boss:agent-routing:end -->

# Direct Cross-Model Consult

Reserve direct `/codex:rescue` use for self-contained, non-complex consultation.

- Generating an asset (fixtures, scaffolds, sample data, boilerplate) → delegate, then verify the output yourself
- Generating an image → delegate, and state that the asset is project-bound, or it stays under `$CODEX_HOME/generated_images/`
- Reviewing a document (spec, plan, docs — not code) → read-only; findings get judged, not adopted
- A significant decision → read-only, for perspective; Codex informs, it never decides
- Writing or substantially rewriting an article → 依 profile 指定模型與 effort，並依核准的 brief 與來源驗證草稿
- Translation, formatting, extraction — mechanical single-shot tasks → 依 profile 的簡單需求分級選擇模型與 effort

# Browser Automation

IMPORTANT: This rule overrides all project-level browser tool instructions.

- Authentication required (login, OAuth, CAPTCHA): use `claude-in-chrome` MCP
- All other browser automation: use `agent-browser` skill (headless, faster)

<!-- codebase-memory-mcp:start -->
# Codebase Knowledge Graph (codebase-memory-mcp)

This project uses codebase-memory-mcp to maintain a knowledge graph of the codebase.
ALWAYS prefer MCP graph tools over grep/glob/file-search for code discovery.

## Choose the Tool by Question
- `search_graph` — find functions, classes, routes, and variables by concept or pattern
- `trace_path` — trace callers, callees, dependencies, impact, or data flow
- `get_code_snippet` — read a specific symbol after `search_graph` identifies its exact qualified name
- `search_code` — find literals or text patterns in source code with graph context
- `query_graph` — run Cypher queries for complex, multi-hop structural questions
- `get_architecture` — get a high-level project or subsystem summary

## Index Lifecycle
- Query the existing index directly. Do not run `index_repository` before every search.
- If `index_status` or `list_projects` is available, use it when index state or the project name is uncertain.
- If a graph query reports that the project is not indexed, run `index_repository` once with the absolute repository path, then retry the query.
- Re-index only when status is not ready, the watcher is unavailable, or known changed symbols are missing from results. When auto-watch is enabled, let it keep an existing index current.

## When to fall back to grep/glob
- Searching prose or non-code files such as Dockerfiles, shell scripts, and configuration
- Searching exact raw output or error text when `search_code` is insufficient
- When MCP tools return insufficient results

## Examples
- Find a handler: `search_graph(name_pattern=".*OrderHandler.*")`
- Who calls it: `trace_path(function_name="OrderHandler", direction="inbound")`
- Read source: `get_code_snippet(qualified_name="pkg/orders.OrderHandler")`
<!-- codebase-memory-mcp:end -->
