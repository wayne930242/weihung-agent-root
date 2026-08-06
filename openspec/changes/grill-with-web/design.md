## Context

`grill-with-docs` already runs structured interviews in the terminal and writes
CONTEXT.md/ADRs as decisions crystallize. The request here is to make that interview
happen in a browser instead, with a live decision-tree visualization next to it, without
losing any fidelity of the real `claude` CLI experience (permission prompts, tool use,
slash commands) — and without requiring the user to ever switch back to a terminal
mid-session.

This system was designed collaboratively (brainstorming session, 2026-08-06), including
live research into prior art and into Anthropic's own issue tracker for known failure
modes of session resumption. That research directly shaped the central decision below.

## Goals / Non-Goals

**Goals:**
- Full-fidelity interactive `claude` CLI, not a simplified/headless chat approximation.
- A live, incrementally-updated decision tree the user can watch grow as the interview
  progresses, with a way to jump from a resolved decision to the document it produced.
- Zero terminal-switching required to complete a grill — only the final artifacts need
  to reach the invoking session.
- Reuse `grill-with-docs`'s document-writing behavior unmodified.

**Non-Goals:**
- Resuming or continuing the invoking session's own conversation — explicitly rejected,
  see Decisions.
- A general-purpose "browser GUI for any Claude Code session" primitive. The
  infrastructure here should be *written* generically enough to extract later, but this
  change ships `grill-with-web` only. No second consumer exists yet (YAGNI).
- In-GUI editing of generated documents — the doc preview panel is read-only.
- Multi-user/multi-viewer support — this is a single-user, session-scoped tool.

## Decisions

### D1: Always spawn a fresh, independent `claude` session — never `--resume`/`--continue`

The obvious approach — resume the invoking session so the web interview inherits full
chat history — was rejected. Anthropic's issue tracker documents unresolved,
"not planned" data-corruption risk when a session's JSONL transcript is touched by more
than one `--resume`/`--continue` process: conversation-tree forking from concurrent
writes ([#48270](https://github.com/anthropics/claude-code/issues/48270)), parentUuid
chain corruption on resume ([#36583](https://github.com/anthropics/claude-code/issues/36583)),
and silent writer failure after a CLI upgrade ([#53417](https://github.com/anthropics/claude-code/issues/53417)).
None of this is fixable from within this skill.

**Alternative considered:** resume/continue with a warning telling the user not to type
in the original terminal concurrently. Rejected — the corruption modes above aren't all
concurrency-triggered (e.g. #36583, #53417), so the warning wouldn't fully cover the risk,
and it would require the user to remember a constraint for the entire session.

**Consequence:** the web session only gets what's in its seed prompt (topic + background
+ relevant file paths), not the invoking session's chat history. Accepted — the stated
goal was always "only the result needs to come back," not "full history in both places."
Second-order benefit: because the two sessions never touch the same transcript file, the
user can freely use the original terminal concurrently with zero risk.

### D2: PTY-wrapped full interactive CLI (xterm.js), not headless/SDK-driven

**Alternatives considered:**
- **Headless** (`claude -p --output-format=stream-json`, or driving the Claude Agent SDK's
  `query()` directly): simpler to render (clean structured events, no ANSI), no PTY/native
  addon dependency. Rejected because it doesn't give full CLI fidelity — permission
  prompts and some interactive behaviors work differently in headless mode, and the user
  explicitly wants "exactly like really being in Claude Code."
- **PTY-wrap the invoking session's own process**: technically impossible — the skill
  invocation is itself running inside that process; it cannot retroactively wrap itself.

Prior art (researched): [siteboon/claudecodeui](https://github.com/siteboon/claudecodeui)
and [vultuk/claude-code-web](https://github.com/vultuk/claude-code-web) both use
`node-pty` + xterm.js + WebSocket for exactly this pattern, confirming it's a proven
approach for full-fidelity browser terminals.

### D3: Single Deno process (backend + static frontend host), `node-pty` via npm compat

One Deno process spawns the PTY-wrapped `claude` process, serves the Next.js static
export (`output: 'export'` — Next.js used purely as a frontend build tool, no runtime
server), and exposes one WebSocket multiplexing PTY I/O + `TREE.json` change events +
doc-preview requests.

**Alternatives considered:**
- **Node.js backend** (what all surveyed prior art uses): rejected — user preference for
  Deno.
- **Deno-native PTY via FFI** ([sigmaSd/deno-pty](https://github.com/sigmaSd/deno-pty)):
  avoids any Node dependency, but is a low-adoption (~9 stars), unaudited project.
  Rejected as too risky for the core I/O path; kept as a documented fallback option.
- **Node.js sidecar dedicated to `node-pty`**, Deno for everything else: most proven,
  lowest-risk path, but reintroduces a Node runtime and an extra process/IPC hop.
  Rejected as the primary approach but is the documented fallback if `npm:node-pty`
  proves unstable under Deno (see Risks).
- **Deno has no native PTY support**: confirmed via research — `Deno.Command` only
  provides piped stdio, no real PTY allocation ([denoland/deno#3994](https://github.com/denoland/deno/issues/3994),
  open since 2020; an experimental `Deno.openPty()` PR was closed unmerged).

`npm:node-pty` under Deno requires `node-pty@1.1.0-beta37`+ (older versions crash —
[denoland/deno#31032](https://github.com/denoland/deno/issues/31032)) and Deno's
`Pipe.prototype.open` support, merged [2025-12](https://github.com/denoland/deno/pull/31624).
This is a recently-viable path — treat as **unverified in this environment until the
first implementation smoke test**, not as a settled fact.

### D4: `TREE.json` is Claude-authored structured data, not inferred from the transcript

The web-session Claude writes `TREE.json` incrementally as branches resolve (same
discipline `grill-with-docs` already applies to CONTEXT.md), rather than the frontend
or a separate process trying to infer tree structure by parsing conversation transcripts.

**Alternative considered:** post-hoc inference from the raw transcript/PTY output via a
second LLM call or heuristic parsing. Rejected — transcript format is an internal
implementation detail of Claude Code (not a stable contract) and inference would be lossy
and error-prone compared to the source (the interviewing Claude) simply stating structure
as it goes.

### D5: Tree panel's per-node input is a convenience entry point into the single PTY stdin, not a parallel channel

Every node gets a small input box, but text submitted there is sent to the *same* PTY
stdin the terminal panel uses — never a separate mechanism for getting Claude to respond
to a specific node. The terminal always echoes whatever was typed, so there is exactly
one conversation thread regardless of which panel the user types in.

**Alternative considered:** genuinely independent per-node conversations, requiring a
mechanism for Claude to address a specific node's thread. Rejected — this would mean
multiple concurrent conversations with one `claude` process (which doesn't support that),
and directly contradicts the requirement that the terminal panel fully match real
Claude Code behavior (a real CLI session has one linear input stream).

### D6: Split-view layout, terminal + tree both always visible

Considered three layouts (mocked up and reviewed with the user): terminal-primary with a
collapsible tree rail, tree-primary with a terminal console drawer, and an even
split with a draggable divider. Chose the even split — continuous ambient visibility of
the tree is the actual point of this tool; collapsing it by default (rail option) would
undercut that, while making it the dominant view (drawer option) would cramp the primary
moment-to-moment typing interaction.

### D7: Op-sec minimal visual theme, fixed regardless of OS light/dark preference

User-approved via mockup comparison. Tokens: background `#0a0c0b`, panel `#101211`,
border `#242825`, foreground `#d7ddd4`, dim text `#5c655e`, accent `#9dff5c`, monospace
throughout, no glow/scanlines. Modeled on modern security-tooling aesthetics (Burp Suite,
tmux-style density) rather than retro CRT. This is a deliberately committed visual world,
not meant to respond to `prefers-color-scheme`.

## Risks / Trade-offs

- **[Risk] `npm:node-pty` under Deno is a newly-viable, lightly-battle-tested path** and
  could fail to build or misbehave in a given environment.
  → **Mitigation**: verify with a real smoke test early in implementation (Task 1, before
  building anything on top of it). Documented fallback: a small Node.js sidecar process
  dedicated to `node-pty`, with the Deno process talking to it over IPC. Fail loudly on
  build failure — no silent degraded mode.
- **[Risk] Losing prior conversation history in the web session** (accepted consequence
  of D1) could mean the web-session Claude lacks context the user assumed it had.
  → **Mitigation**: the seed prompt explicitly carries topic + background + relevant file
  paths; `grill-with-web`'s SKILL.md is responsible for making that seed prompt
  sufficiently complete, not for silently degrading to "figure it out."
- **[Risk] Browser tab closed / connection lost mid-session** could look like data loss.
  → **Mitigation**: PTY process persists server-side regardless of WebSocket connection
  state; reopening the URL reconnects to the live session. Not a failure mode, by design.
- **[Risk] Browser auto-open fails silently** (confirmed unreliable under WSL without
  extra tooling, verified during this design's research).
  → **Mitigation**: always print the full URL as a fallback; never rely on auto-open
  succeeding.
- **[Trade-off] Single Deno process handles both PTY spawning and HTTP/WS serving** —
  simpler operationally (one process to manage) but couples their failure domains (a
  crash in one takes down the other).
  → Accepted: the whole tool is session-scoped and short-lived; process isolation between
  PTY and serving isn't worth the added complexity for this use case.

## Migration Plan

This is new, additive functionality — no existing skill or system is modified.
- Rollout is simply adding `skills/grill-with-web/` to the repo; no flag/toggle needed,
  since it's a new, separately-invoked skill.
- First-run cost: Deno dependency resolution (`npm:node-pty` install) happens on first
  invocation, not at install time — the skill should surface this wait explicitly rather
  than appearing to hang.
- No rollback concern beyond removing the skill directory; it has no effect on
  `grill-with-docs` or any other existing skill.

## Open Questions

- **Environment verification for `npm:node-pty` under Deno** is still outstanding — this
  design proceeds on the research finding that it's viable as of recent Deno/node-pty
  releases, but the first implementation task must confirm this directly (see Risks).
- **Timeout value for the invoking session's completion poll** (Session Lifecycle step 4
  in the original brainstorm) — not yet pinned to a specific duration; left for the
  implementation task to decide.
