## Why

Grilling interviews (`grill-with-docs`) currently happen entirely in the terminal. For
structured discussions where staying aligned with the agent's evolving mental model
matters — the actual goal of grilling — a linear terminal transcript makes it hard to
see the shape of the decision tree as it forms. The user wants the whole conversation to
be able to happen in a browser instead, with a live node-based tree next to it, so
alignment is visible continuously rather than reconstructed after the fact.

## What Changes

- Add a new `grill-with-web` skill that spins up a session-scoped browser GUI for
  running a `grill-with-docs` interview.
- The interview runs as a real, full-fidelity interactive `claude` CLI session
  (permission prompts, tool use, everything) rendered in-browser via a PTY-backed
  terminal — not a simplified or headless chat approximation.
- **A brand-new, independent `claude` session is spawned for every web-driven grill** —
  never `--resume`/`--continue` of the session that invoked the skill. This is a
  deliberate safety choice (see design.md) with a real trade-off: the web session does
  not inherit prior chat history, only a seed prompt with topic/background.
- A live decision-tree panel renders alongside the terminal, driven by a structured
  `TREE.json` file the web-session Claude writes incrementally as branches resolve.
  Clicking a resolved node with a linked ADR opens a read-only preview of that document.
- All of `grill-with-docs`'s existing document-writing behavior (CONTEXT.md, sparing
  ADRs) is reused unmodified; this change adds one new deliverable — a tree summary
  document with an embedded Mermaid diagram.
- The invoking terminal session blocks (pollable, cancellable) until the web session
  signals completion, then reports the written file paths back.

## Capabilities

### New Capabilities

- `grill-web-orchestration`: the `grill-with-web` skill's own behavior — computing
  per-session state, building the seed prompt, starting/stopping the backend process,
  detecting completion, reporting results back to the invoking session, and cancellation.
- `grill-web-terminal`: the PTY-backed, full-fidelity terminal experience in the browser
  — spawning the fresh `claude` process, streaming its I/O over WebSocket, surviving
  browser disconnects/reconnects, and the static frontend serving.
- `grill-web-tree`: the live decision-tree — the `TREE.json` schema and incremental
  write discipline, real-time push to the browser, the split-view GUI layout and its
  op-sec visual theme, per-node input as a convenience entry point into the single PTY
  stdin, and the resolved-node document preview panel.

### Modified Capabilities

*(none — `grill-with-docs` is invoked as-is, not modified)*

## Impact

- **New code**: `skills/grill-with-web/` (SKILL.md, NODE-FORMAT.md, a Deno backend
  under `server/`, a Next.js static-export frontend under `web/`).
- **New runtime dependency**: Deno, and `node-pty` (>=1.1.0-beta37) running under Deno's
  npm compatibility layer — a newer, less-proven compatibility path that needs
  environment verification (see design.md for the fallback if it proves unstable).
- **No changes to existing skills** — `grill-with-docs`, `grilling`, and their format
  files (`CONTEXT-FORMAT.md`, `ADR-FORMAT.md`) are consumed as-is.
- **Target project repos** gain one new artifact type when this skill is used:
  `docs/grill/<slug>.md`.
- **This machine's `~/.claude/state/`** gains a new subtree for per-session `TREE.json`
  scratch state, mirroring the existing `claude/hooks/` state-dir convention.
