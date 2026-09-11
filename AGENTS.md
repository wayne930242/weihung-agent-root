Never use Simplified Chinese. Always use Traditional Chinese for all communication.
All prompts and agent instructions must be in English.

提示詞、文件與文章應直接陳述期望行為，避免不必要的防禦性用語。

Source-changing work invokes `aaaav-do` and states its Alignment and Reality anchor before the first production edit.

# Routing

執行 `boss-say` 或選擇委派模型前，讀取 `~/.codex/skills/managing-model-preferences/model-preference-profile.md`；在本專案內使用 `skills/managing-model-preferences/model-preference-profile.md`。依當期 profile 明確指定模型與 effort。調整偏好使用 `managing-model-preferences` skill。

IMPORTANT: Before responding to a significant request, choose one owner:

- A named or exact specialized skill -> use it.
- Explanation or comparison -> `providing-knowledge`.
- Research -> `investigating`.
- Check, audit, or review -> `inspecting`.
- Human feedback on working output -> `human-feedback`.
- Any source-changing work -> `aaaav-do`.
- A user-owned unresolved decision -> `grilling`.

Specialized skills return source-changing work to `aaaav-do`; the
finding travels, the work does not restart.

# Working Agreements

- Show your reasoning. When making decisions, explain the logic so the user can verify your thinking.
- Proactively report problems. If you see something suboptimal, say it immediately, even if the user did not ask.
- Read before write. Understand existing patterns before editing.
- Run relevant verification before claiming success.
- Commit messages must not mention AI tools.

# Scope Boundaries

- Keep general working agreements here in `AGENTS.md`.
- Put approval policy in Codex `rules/*.rules`, not in prose.
- Put automation behavior in Codex `hooks.json` and `hooks/`, not in prose.
- Put specialized delegation behavior in Codex `agents/*.toml`, not in prose.

# Windows / WSL Path Interoperability

- When running in WSL, translate local attachment paths written as `C:\\...`
  (or another Windows drive path) to `/mnt/<drive>/...` before accessing them.
  Use `wslpath -u` when available.
- Quote translated paths because Windows user and temporary directories may
  contain spaces.
- Do not conclude that a Windows clipboard or temporary file has expired only
  because its unconverted Windows path is unavailable inside WSL. Check the
  translated path first.

# Project Guidance Interoperability

- If the current workspace contains a `CLAUDE.md` and no project-level `AGENTS.md` or `GEMINI.md`, treat `CLAUDE.md` as the authoritative project guide and inspect it before taking project-specific actions.
- If the current workspace contains `.claude/skills/`, check for relevant project-specific skills in that directory when addressing project workflows.

# Browser Automation

- If the current harness has a browser tool and the task does not require login, use the faster non-auth path first.
- If the task requires authentication, OAuth, or CAPTCHA, stop and use an authenticated browser path only when the harness supports it and the user expects it.

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
