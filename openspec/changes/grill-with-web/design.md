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
- In-GUI editing of generated documents — the doc preview panel is read-only.
- Multi-user/multi-viewer support — this is a single-user, session-scoped tool.
- A generic *plugin/extension-point* architecture in `open-gui` for arbitrary future
  side-panel content. `open-gui` owns one specific, generically-typed tree UI (see D9) —
  not an open-ended plugin API. Extending node rendering later means adding a new `type`
  case, not designing an extension mechanism now (YAGNI still applies to *that*).

> **Revision (2026-08-07):** an earlier version of this design treated "a general-purpose
> browser GUI for any Claude Code session" as an explicit Non-Goal/YAGNI and planned to
> ship `grill-with-web` only, with infrastructure merely "written generically enough to
> extract later." That call is reversed — see D8. The user requested the extraction
> happen now, as an independently-usable `open-gui` skill, specifically because the tree
> panel itself needs to be generic (typed nodes, not grilling-specific) for `open-gui` to
> be a real standalone tool rather than grilling infrastructure in disguise.

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

### D3: Deno process (HTTP/WS + static frontend host) + Node.js sidecar for `node-pty`

**Superseded by smoke test (2026-08-07).** The originally-proposed primary approach —
`npm:node-pty` running directly under Deno's npm compatibility layer — was smoke-tested
per Task 1.1 and **fails**: `node-pty`'s native addon does build under Deno, and
`pty.fork()` succeeds, but the read path (`node:tty`'s `tty.ReadStream(fd)` wrapping the
PTY master fd) never emits `data` or `exit` events under Deno — confirmed with a minimal
`/bin/echo` case that should terminate and emit output almost immediately. This is a
deeper Node-compat gap (fd/tty handle bridging), not something fixable from within this
skill.

Separately (and confirmed to affect **both** runtimes, not just Deno): the extracted
`spawn-helper` binary loses its executable bit on this machine regardless of installer
(`deno install`/`deno approve-scripts` and plain `npm install` both reproduce it) —
`chmod +x` restores it and `node-pty` then works correctly under plain Node.js
(`SMOKE_TEST_PASS` confirmed separately). This is an environment/packaging quirk to
defend against defensively (e.g. the sidecar's startup asserts+fixes the bit before
first spawn), not a reason to distrust `node-pty` itself — plain Node.js is the proven,
widely-used path all surveyed prior art already relies on.

Per the fallback this
design already specified, **the Node.js sidecar is now the primary approach**, not a
documented fallback:

- A small Node.js process owns `node-pty` exclusively: spawns the PTY-wrapped `claude`
  process, reads/writes it, and exposes that over a local IPC channel (a Unix domain
  socket carrying newline-delimited JSON, chosen over stdio pipes so the sidecar can be
  restarted independently of the parent's stdio lifecycle).
- The Deno process spawns and supervises this sidecar, serves the Next.js static export
  (`output: 'export'` — Next.js used purely as a frontend build tool, no runtime server),
  and exposes one WebSocket multiplexing PTY I/O + `TREE.json` change events +
  doc-preview requests — relaying PTY I/O to/from the sidecar over the IPC channel.

**Alternatives considered:**
- **`npm:node-pty` directly under Deno**: the original primary approach. Rejected per the
  smoke-test finding above.
- **Node.js backend** (what all surveyed prior art uses): rejected — user preference for
  Deno for the HTTP/WS/static-serving layer; the sidecar isolates the unavoidable Node
  dependency to exactly the one thing that needs it.
- **Deno-native PTY via FFI** ([sigmaSd/deno-pty](https://github.com/sigmaSd/deno-pty)):
  avoids any Node dependency, but is a low-adoption (~9 stars), unaudited project.
  Rejected as too risky for the core I/O path.
- **Deno has no native PTY support**: confirmed via research — `Deno.Command` only
  provides piped stdio, no real PTY allocation ([denoland/deno#3994](https://github.com/denoland/deno/issues/3994),
  open since 2020; an experimental `Deno.openPty()` PR was closed unmerged).

**Consequence:** two runtimes (Deno + Node.js) and one extra IPC hop for all PTY I/O.
Accepted — this is exactly the trade-off the original design flagged as the fallback's
cost, now realized. The sidecar is owned by `open-gui`'s `server/`; `grill-with-web`
never talks to it directly.

### D4: `TREE.json` is Claude-authored structured data, not inferred from the transcript

The session's Claude writes `TREE.json` incrementally as nodes are added/resolved (same
discipline `grill-with-docs` already applies to CONTEXT.md), rather than the frontend or
a separate process trying to infer tree structure by parsing conversation transcripts or
PTY ANSI output. This is now an `open-gui` requirement (the schema lives in `open-gui`'s
`NODE-FORMAT.md`), not grilling-specific — see D9.

**Alternative considered:** post-hoc inference from the raw transcript/PTY output via a
second LLM call or heuristic parsing. Rejected — transcript format is an internal
implementation detail of Claude Code (not a stable contract), PTY output is unstructured
ANSI, and inference would be lossy and error-prone compared to the source (the session's
own Claude) simply stating structure as it goes. This principle is why D9's `question`
node type mirrors `AskUserQuestion` calls via an *explicit instructed second write*
rather than trying to capture the tool's rendered UI from the PTY stream.

### D5: Tree panel's per-node input is a convenience entry point into the single PTY stdin, not a parallel channel

Every node gets a small input affordance, but whatever text it produces is sent to the
*same* PTY stdin the terminal panel uses — never a separate mechanism for getting Claude
to respond to a specific node. The terminal always echoes whatever was submitted, so
there is exactly one conversation thread regardless of which panel the user interacts
with. `question`-type nodes render this as clickable option cards (see D9) plus an
"Other" free-text field and a notes field, mirroring `AskUserQuestion`'s own interface;
all other node types get a plain free-text box. Whichever form it takes, submission
funnels into the same PTY stdin write.

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
moment-to-moment typing interaction. This is `open-gui`'s default layout, always on
(there is no tree-less mode); a session that never writes any tree nodes simply shows an
empty tree panel.

### D7: Op-sec minimal visual theme, fixed regardless of OS light/dark preference

User-approved via mockup comparison. Tokens: background `#0a0c0b`, panel `#101211`,
border `#242825`, foreground `#d7ddd4`, dim text `#5c655e`, accent `#9dff5c`, monospace
throughout, no glow/scanlines. Modeled on modern security-tooling aesthetics (Burp Suite,
tmux-style density) rather than retro CRT. This is a deliberately committed visual world,
not meant to respond to `prefers-color-scheme`.

### D8: Split into two skills — `open-gui` (independent, general-purpose) and `grill-with-web` (thin consumer)

Reverses the original design's Non-Goal (see Revision note under Goals/Non-Goals). The
user's requirement was concrete, not aesthetic: the tree needs distinct node types
(`decision`/`question`/`artifact`/`info`) so the frontend can render each differently —
and that generic taxonomy only makes sense if it's not scoped to grilling. Splitting now,
rather than after a second consumer materializes, is what makes `open-gui` genuinely
usable standalone (per the user's explicit requirement) instead of grilling
infrastructure that merely *could* be extracted later.

**Boundary:**
- `open-gui` owns: PTY spawn + Node sidecar + WebSocket + static frontend serving
  (`open-gui-terminal`), the generic typed node tree UI/schema/live-push/preview
  (`open-gui-tree`), and its own thin per-session orchestration — state dir, seed prompt
  delivery, PID/port recording, browser open (`open-gui-session`). It is invocable
  directly by a user for any `claude` session, with no grilling awareness at all.
- `grill-with-web` owns: constructing the grilling-specific seed prompt (topic,
  background, file paths, instructions to run `grill-with-docs` and populate the tree
  with `decision`-type nodes), calling `open-gui` to start the session, polling the
  tree's top-level status for completion, stopping the `open-gui` backend via its
  recorded PID (on completion or manual cancel), and reporting document paths back. It
  ships **no server or frontend code** — `open-gui`'s is reused unmodified.
- Lifecycle asymmetry is intentional (see D9's "fully passive" framing): `open-gui`
  never polls for completion or shuts itself down on its own — a standalone `open-gui`
  session simply runs until the user closes it. `grill-with-web` is the one that adds
  the completion-poll-and-shutdown behavior, as a layer on top, not a feature `open-gui`
  provides generically. This means `open-gui` must still *record* the backend's PID (and
  port) in the per-session state directory even though it never reads or acts on that
  file itself — otherwise no external caller could stop it.

**Alternative considered:** keep everything inside `grill-with-web` and revisit
extraction only when a second real consumer shows up (original YAGNI framing). Rejected
per explicit user direction — the generic-node-type requirement effectively *is* that
second consumer's design constraint, arriving before rather than after the fact.

### D9: Generic, discriminated-union node types — not a single grilling-shaped node schema

`open-gui`'s `NODE-FORMAT.md` defines a base node (`id`, `type`, `parent`, `title`) plus
per-`type` payload:

- `decision`: `recommendation`, `status` (`open`/`resolved`), `resolution` (required once
  resolved), optional `doc` (a file path for the read-only preview panel). This is what
  `grill-with-web` populates for grilling branches; `doc` is where it points at an ADR.
- `question`: `prompt`, `options[]` (`label`, optional `description`), `status`
  (`open`/`resolved`), `answer` once resolved. The UI always additionally renders an
  "Other" free-text field and a notes field alongside the option cards — mirroring
  `AskUserQuestion`'s real interface (custom replies and per-selection notes are core to
  that tool, not edge cases) — so `answer` may be a selected option's label, custom free
  text, or both plus a note.
- `artifact`: `path` — a **local file path** to preview/embed (not a published claude.ai
  URL: those are private-by-default and would hit auth inside an iframe). Reuses the same
  doc-preview handler as `decision`'s `doc` field (Task 3.4) — no separate code path.
- `info`: `text` (markdown) — static, non-interactive.

Per-type validation (which fields are required for which `status`) generalizes the
schema test already planned in Task 4.2.

**Alternative considered:** a single node shape with optional fields for every concern
(recommendation, prompt, options, path, text all present but mostly unused per node).
Rejected — a discriminated union lets the frontend render distinct, purpose-built UI per
node type instead of one fixed template guessing which fields matter, and keeps
`grill-with-web`'s own instructions simple (it only ever emits `decision`, optionally
`question`, nodes).

## Risks / Trade-offs

- **[Risk] `npm:node-pty` under Deno is a newly-viable, lightly-battle-tested path** and
  could fail to build or misbehave in a given environment.
  → **Realized**: smoke test (Task 1.1) confirmed it fails — see D3. Mitigation applied:
  Node.js sidecar dedicated to `node-pty`, Deno process talks to it over IPC. Fail loudly
  on build/spawn failure — no silent degraded mode.
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
- **[Trade-off] Deno process + Node.js sidecar, connected over local IPC** — two runtimes
  and one extra hop for all PTY I/O, instead of one process handling everything.
  → Accepted: this is the realized cost of D3's fallback; the alternative (PTY under
  Deno directly) does not work in practice (smoke-tested). The whole tool is
  session-scoped and short-lived, so the added process isn't an operational burden.
- **[Risk] `open-gui`'s fully-passive lifecycle (D8) means a forgotten standalone session
  leaks a running `claude` process + backend indefinitely** if the user never closes it.
  → **Mitigation**: this is accepted as the correct default for a general-purpose tool —
  auto-closing a session the user is actively using would be worse. `open-gui`'s SKILL.md
  documents how to list/stop sessions manually (via the recorded PID/port in
  `~/.claude/state/`); `grill-with-web` is the one consumer that needs and implements
  auto-shutdown, on top, for its own bounded flow.

## Migration Plan

This is new, additive functionality — no existing skill or system is modified.
- Rollout is adding `skills/open-gui/` and `skills/grill-with-web/` to the repo; no
  flag/toggle needed, since both are new, separately-invoked skills.
- First-run cost: dependency resolution (Deno's own deps, and the Node sidecar's
  `npm install` for `node-pty`) happens on first invocation of `open-gui`, not at install
  time — the skill should surface this wait explicitly rather than appearing to hang.
- No rollback concern beyond removing the skill directories; neither has any effect on
  `grill-with-docs` or any other existing skill. `grill-with-web` depends on `open-gui`
  being present; removing `open-gui` alone breaks `grill-with-web`.

## Open Questions

- **Timeout value for the invoking session's completion poll** (Session Lifecycle step 4
  in the original brainstorm) — not yet pinned to a specific duration; left for the
  implementation task to decide.
- **Exact IPC message shape between the Deno process and the Node sidecar** (D3) — newline-
  delimited JSON over a Unix domain socket is decided; the specific message types (PTY
  data chunk, resize, write, spawn, exit) are an implementation detail for Task 2.
