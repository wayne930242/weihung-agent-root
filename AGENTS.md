Never use Simplified Chinese. Always use Traditional Chinese for all communication.

# Routing

IMPORTANT: Before responding to any significant request, classify and route:

- An existing external or built-in skill applies -> use that skill directly
- Development task (implement, design, debug, deploy) -> `leveraging-tasks` skill
- Question (explain, what is, how does) -> `providing-knowledge` skill
- Investigation (research, find out, current state of) -> `investigating` skill
- Inspection (check, audit, verify, review) -> `inspecting` skill

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

# Browser Automation

- If the current harness has a browser tool and the task does not require login, use the faster non-auth path first.
- If the task requires authentication, OAuth, or CAPTCHA, stop and use an authenticated browser path only when the harness supports it and the user expects it.

<!-- codebase-memory-mcp:start -->
# Codebase Knowledge Graph (codebase-memory-mcp)

This project uses codebase-memory-mcp to maintain a knowledge graph of the codebase.
ALWAYS prefer MCP graph tools over grep/glob/file-search for code discovery.

## Priority Order
1. `search_graph` — find functions, classes, routes, variables by pattern
2. `trace_path` — trace who calls a function or what it calls
3. `get_code_snippet` — read specific function/class source code
4. `query_graph` — run Cypher queries for complex patterns
5. `get_architecture` — high-level project summary

## When to fall back to grep/glob
- Searching for string literals, error messages, config values
- Searching non-code files (Dockerfiles, shell scripts, configs)
- When MCP tools return insufficient results

## Examples
- Find a handler: `search_graph(name_pattern=".*OrderHandler.*")`
- Who calls it: `trace_path(function_name="OrderHandler", direction="inbound")`
- Read source: `get_code_snippet(qualified_name="pkg/orders.OrderHandler")`
<!-- codebase-memory-mcp:end -->
