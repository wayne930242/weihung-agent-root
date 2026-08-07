## Why

Grilling interviews (`grill-with-docs`) currently happen entirely in the terminal. For
structured discussions where staying aligned with the agent's evolving mental model
matters — the actual goal of grilling — a linear terminal transcript makes it hard to
see the shape of the decision tree as it forms. The user wants the whole conversation to
be able to happen in a browser instead, with a live node-based tree next to it, so
alignment is visible continuously rather than reconstructed after the fact.

## What Changes

This change ships as **two skills**, split so the browser-GUI infrastructure is
independently usable rather than locked inside the grilling use case (see design.md D8):

- **`open-gui`** (new, standalone, general-purpose skill): spins up a session-scoped
  browser GUI wrapping a real, full-fidelity interactive `claude` CLI session
  (permission prompts, tool use, everything) via a PTY-backed terminal — not a
  simplified or headless chat approximation. A live, generically-typed node tree
  (`decision` / `question` / `artifact` / `info`) renders alongside the terminal, driven
  by a structured `TREE.json` file the session's Claude writes incrementally. Usable on
  its own for any Claude Code session, not just grilling. **Fully passive lifecycle**:
  once started it never proactively closes the session — that is left entirely to
  whichever skill or user started it.
- **`grill-with-web`** (new, thin consumer skill — the GUI version of `grill-with-docs`):
  builds a grilling-specific seed prompt and starts an `open-gui` session with it. **A
  brand-new, independent `claude` session is spawned for every web-driven grill** — never
  `--resume`/`--continue` of the session that invoked the skill. This is a deliberate
  safety choice (see design.md) with a real trade-off: the web session does not inherit
  prior chat history, only a seed prompt with topic/background. All of
  `grill-with-docs`'s existing document-writing behavior (CONTEXT.md, sparing ADRs) is
  reused unmodified; this change adds one new deliverable — a tree summary document with
  an embedded Mermaid diagram, linked from resolved `decision` nodes for read-only
  preview. Unlike `open-gui` on its own, `grill-with-web` actively polls for completion
  and stops the session: the invoking terminal session blocks (pollable, cancellable)
  until the web session signals completion via the tree's top-level status, then reports
  the written file paths back.

## Capabilities

### New Capabilities

- `open-gui-terminal`: the PTY-backed, full-fidelity terminal experience in the browser
  — spawning a fresh `claude` process, streaming its I/O over WebSocket, surviving
  browser disconnects/reconnects, and the static frontend serving.
- `open-gui-tree`: the live, generically-typed node tree — the `TREE.json` schema
  (discriminated union over `decision` / `question` / `artifact` / `info` node types),
  incremental write discipline, real-time push to the browser, the split-view GUI layout
  and its op-sec visual theme, per-node interaction (free-text input, and for `question`
  nodes, clickable options plus an "Other" free-text reply and a notes field, mirroring
  the `AskUserQuestion` tool's own interface) as a convenience entry point into the
  single PTY stdin, and the resolved-node document/artifact preview panel.
- `open-gui-session`: the `open-gui` skill's own thin orchestration — computing the
  per-session state directory, delivering the seed prompt, recording the backend
  process's PID/port for an external caller to use, starting the backend, and browser
  auto-open with a URL fallback. Deliberately has no completion detection or
  auto-shutdown logic — the session runs until the user or a calling skill stops it.
- `grill-web-orchestration`: the `grill-with-web` skill's own behavior — building the
  grilling-specific seed prompt (instructing the target session to run `grill-with-docs`
  and populate `open-gui`'s tree with `decision`-type nodes), starting an `open-gui`
  session with it, polling the tree's top-level completion status, stopping the
  `open-gui` backend (via its recorded PID) on completion or manual cancellation, and
  reporting the written document paths back to the invoking session.

### Modified Capabilities

*(none — `grill-with-docs` is invoked as-is, not modified)*

## Impact

- **New code**: `skills/open-gui/` (SKILL.md, NODE-FORMAT.md, a Deno backend under
  `server/` that talks to a Node.js sidecar for `node-pty`, a Next.js static-export
  frontend under `web/`) and `skills/grill-with-web/` (SKILL.md only — no server/web
  code, it reuses `open-gui`'s).
- **New runtime dependencies**: Deno, Node.js, and `node-pty` (>=1.1.0-beta37) running
  under a small Node.js sidecar process (not directly under Deno's npm compatibility
  layer — verified unstable, see design.md D3).
- **No changes to existing skills** — `grill-with-docs`, `grilling`, and their format
  files (`CONTEXT-FORMAT.md`, `ADR-FORMAT.md`) are consumed as-is.
- **Target project repos** gain one new artifact type when `grill-with-web` is used:
  `docs/grill/<slug>.md`.
- **This machine's `~/.claude/state/`** gains a new subtree for per-session `TREE.json`
  scratch state under `open-gui/`, mirroring the existing `claude/hooks/` state-dir
  convention. `grill-with-web` sessions use this same subtree (it delegates session
  startup to `open-gui`).
