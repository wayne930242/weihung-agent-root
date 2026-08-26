Never use Simplified Chinese. Always use Traditional Chinese for all communication.

# Routing

IMPORTANT: Before responding to a significant request, choose one owner:

- A named or exact specialized skill -> use it.
- Explanation or comparison -> `providing-knowledge`.
- Research -> `investigating`.
- Check, audit, or review -> `inspecting`.
- Any source-changing work -> `leveraging-tasks`.
- A user-owned unresolved decision -> `grilling`.

Specialized skills return source-changing work to `leveraging-tasks`. Entering
that owner does not require SDD files: clear local work with little future reuse
stays inline, while durable decisions and coordination leave phased artifacts
under `docs/specs/`.

# Working Agreements

- Show your reasoning. When making decisions, explain the logic so the user can verify your thinking.
- Proactively report problems. If you see something suboptimal, say it immediately, even if the user did not ask.
- Read before write. Understand existing patterns before editing.
- Do only what is asked. No unrelated cleanup.
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
