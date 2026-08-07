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

**Revision (2026-08-07): reversed. Superseded by D11.** The rejection reason above —
"permission prompts and interactive behaviors work differently in headless mode" — turned
out to be wrong about *why* headless was worse, not about whether it was different. Hours
of live debugging on the PTY path (D5) went into reverse-engineering `AskUserQuestion`'s
raw-mode keystroke protocol and fighting paste-detection, and the resulting mechanism was
still fundamentally fragile: `TREE.json`'s node-authoring lags the terminal's live state
by construction (D4), so no frontend heuristic can reliably tell "which node is the
terminal showing right now" — confirmed live when a brand-new `AskUserQuestion` menu was
already on screen with zero corresponding tree node. Separately, the user's own use of the
GUI surfaced a real product complaint headless was never going to have: the question's
content rendering twice (once as the live terminal widget, once as the tree's question
node) once both existed.

What actually motivated D2's rejection was never re-examined until directly researched
(2026-08-07): the Agent SDK's `canUseTool` callback receives `AskUserQuestion` calls with
their full structured `questions` payload (same shape as this doc's `question` node type)
and *blocks* until the callback resolves — meaning "ask a real person, in a browser, who
might take minutes" is a documented, intended use case, not a hack. This was verified
live, not assumed: a Deno spike (`npm:@anthropic-ai/claude-agent-sdk`) drove a real session
through streaming input, held `canUseTool` pending for 20s inside the callback (simulating
real think time), and confirmed the session stayed alive and correctly continued after the
delayed answer — including a `rate_limit_event` arriving mid-wait, proof the underlying
connection was live, not frozen. See D11.

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
  process, reads/writes it, and exposes that over a local IPC channel — a **TCP loopback
  socket** (`127.0.0.1`, OS-assigned port) carrying newline-delimited JSON, chosen over
  stdio pipes so the sidecar can be restarted independently of the parent's stdio
  lifecycle. Originally a Unix domain socket; changed after two independent failures —
  Deno's `transport: "unix"` has no Windows support at all, and macOS's
  `sockaddr_un.sun_path` length limit broke once the socket path was nested under a long
  state directory. See `PROTOCOL.md` §1.
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

**Revision (2026-08-07): removed entirely, superseded by D11.** D2's reversal removes the
PTY from the picture altogether — no `node-pty`, no Node.js sidecar, no IPC hop. The Deno
process talks to `@anthropic-ai/claude-agent-sdk` directly via a Deno `npm:` specifier
(confirmed working: the package is pure ESM with zero runtime dependencies of its own,
`engines.node >=18`, and the live spike under D11 ran it successfully). This section is
kept for its record of why `node-pty` under Deno doesn't work — not a live concern anymore
since nothing here needs a PTY, but worth keeping if a future decision ever needs it again.

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
node type mirrored `AskUserQuestion` calls via an *explicit instructed second write*
rather than trying to capture the tool's rendered UI from the PTY stream.

**Revision (2026-08-07):** this principle still holds for `decision`/`artifact`/`info`
nodes — Claude still authors `TREE.json` for those, no change. But D11 removes `question`
from what Claude has to write at all: `AskUserQuestion` calls now arrive as structured
data straight from the SDK (see D11), which is *more* reliable than an instructed second
write, not less — no lag, no chance of the instruction being forgotten or the write racing
behind the live tool call. `grill-with-web`'s seed prompt stops asking Claude to emit
`question` nodes; `open-gui`'s schema keeps the type for other, non-`grill-with-web`
consumers that might still want it.

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

**Revision (2026-08-07):** "submission funnels into the PTY stdin" turned out to hide a
real assumption — that the PTY is always at a plain text prompt when a node submits.
Verified against a real `claude` session: `AskUserQuestion` renders as a raw-mode menu
widget, not text. Typing an option's label into it does nothing (a long burst even trips
the same paste-detection that separately broke seed-prompt delivery — see
`SEED_SUBMIT_DELAY_MS` in `main.ts`). The real, empirically-verified protocol: a bare
digit keystroke (no `\r`) for one of the menu's *real* options selects and confirms it in
one step; the widget also appends two trailing entries after the real options ("N+1 Type
something", "N+2 Chat about this") where a digit only moves the highlight and needs a
*separate* `\r` to confirm — and confirming *that* doesn't open a text field inside the
widget, it cancels the tool call and returns to the normal chat prompt, where plain text
works as before. `QuestionNode.js` now sends option selections as bare digits and routes
"Other" through the two-step digit-then-text sequence; notes can no longer be attached in
the same action as an option pick (the digit already confirms and moves on) and go out as
a separate follow-up message instead. **Accepted, unaddressed risk:** this assumes the
selected node's menu is still the live thing on screen at submission time — a stale
node's keystroke lands on whatever the terminal actually shows. No fix attempted for this
staleness risk; `open-gui-tree`'s "Optimistic pending indicator" softens it (a node
already marked pending is a visual hint it was likely already acted on) but does not
close it.

**Revision (2026-08-07): superseded entirely by D11.** The "unaddressed risk" above was
never actually fixable within the PTY model — it's a direct consequence of D4's
Claude-authors-`TREE.json` principle combined with a terminal that updates in real time
and a tree that only updates when Claude chooses to write. D11 removes the PTY stdin as
the answer channel altogether: a `question`-type submission now becomes a WebSocket
message the backend feeds directly into a pending `canUseTool` resolution for that
specific tool call, keyed by the SDK's own tool-use id — there is no "which node is live
on screen" ambiguity to have, because there's no screen. This whole decision (digit
keystrokes, paste-detection timing, the two-step Other sequence) is now dead code once
D11 ships; kept here as the record of what was tried and why it was still fragile even
once correctly implemented.

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

**Revision (2026-08-07):** reversed by explicit user request — real usage surfaced that
"fixed, not OS-following" was read as "doesn't respect the user's own environment,"
specifically Claude Code's own `theme` setting (distinct from the OS-level
`prefers-color-scheme` this decision originally addressed). The system now follows
`~/.claude/settings.json`'s `theme` value: the backend reads it once at startup
(best-effort — missing/unreadable/unrecognized values default to the dark theme above,
preserving the original tokens as the fallback) and sends it to the browser as a `config`
message (`PROTOCOL.md` §2). A parallel light palette was added (background `#f4f6f2`,
panel `#ffffff`, border `#dde3d8`, foreground `#1c211b`, dim text `#6e7a6a`, accent
`#15803d`) sharing the same token structure, applied via a `data-theme` attribute in CSS
and mirrored into the embedded terminal's own xterm color theme so the two panels never
show mismatched themes. The `prefers-color-scheme` non-goal from the original decision
still stands — this follows Claude Code's config, not the OS.

### D8: Split into two skills — `open-gui` (independent, general-purpose) and `grill-with-web` (thin consumer)

Reverses the original design's Non-Goal (see Revision note under Goals/Non-Goals). The
user's requirement was concrete, not aesthetic: the tree needs distinct node types
(`decision`/`question`/`artifact`/`info`) so the frontend can render each differently —
and that generic taxonomy only makes sense if it's not scoped to grilling. Splitting now,
rather than after a second consumer materializes, is what makes `open-gui` genuinely
usable standalone (per the user's explicit requirement) instead of grilling
infrastructure that merely *could* be extracted later.

**Boundary:**
- `open-gui` owns: the session/WebSocket/static frontend serving layer (`open-gui-chat`,
  originally `open-gui-terminal` — a PTY spawn + Node sidecar at the time this decision
  was written, superseded by D11), the generic typed node tree UI/schema/live-push/preview
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

**Revision (2026-08-07): two narrow, mechanical exceptions to "never shuts itself down."**
User-raised, twice, from real usage: (1) closing the browser tab doesn't hand off or
pause anything (deliberate, unchanged — see D10), but nothing was cleaning up the backend
either, so a forgotten tab (or a browser auto-open that silently failed and nobody ever
opened the URL) left the Deno process, its Node sidecar, and the spawned `claude` process
running forever, accumulating across sessions; (2) the wrapped `claude` process exiting
on its own (`/exit`, a crash) left the backend serving a permanently frozen terminal to
whatever's still connected. Both are now handled in `main.ts`: the backend shuts itself
down (a) ~500ms after the wrapped process exits (broadcasting `session:ended` first so a
connected browser can show why — `PROTOCOL.md`), and (b) after 15 minutes with zero open
WebSocket connections, whether from every tab closing or the browser never connecting at
all; any connection within that window cancels the timer. Neither is a reversal of D8/D9
— both are mechanical process/connection-lifecycle facts, not an inference about whether
the *task* is done, which is the specific thing "never shuts itself down" protects.

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
- `artifact`: `kind` (`file` | `url`, default `file`). `file`-kind carries `path` — a
  local file path, reusing the same doc-preview handler as `decision`'s `doc` field
  (Task 3.4), no separate code path. `url`-kind carries `url` — a published claude.ai
  artifact link, iframed directly in the detail pane with an "open in new tab" button.
  **Revision (2026-08-07):** originally this type only supported local paths, on the
  reasoning that claude.ai artifacts are private-by-default and would hit an auth wall in
  an iframe. Reversed by explicit user request — that auth-wall behavior is now an
  accepted trade-off (the iframe shows claude.ai's own sign-in page for a non-shared
  link) rather than a reason to disallow the capability entirely; a public/shared link
  works inline as expected.
- `info`: `text` (markdown) — static, non-interactive.

Per-type validation (which fields are required for which `status`) generalizes the
schema test already planned in Task 4.2.

**Alternative considered:** a single node shape with optional fields for every concern
(recommendation, prompt, options, path, text all present but mostly unused per node).
Rejected — a discriminated union lets the frontend render distinct, purpose-built UI per
node type instead of one fixed template guessing which fields matter, and keeps
`grill-with-web`'s own instructions simple (it only ever emits `decision`, optionally
`question`, nodes).

### D10: Deterministic `--session-id` at spawn, manual (not automatic) hand-off to a normal terminal

Verified locally (`claude --help`): `--session-id <uuid>` pins a session's id at spawn,
and `-r/--resume <id>` resumes it later. This means the browser-spawned session can be
picked up from an ordinary terminal after the fact — a real capability, not a workaround.

**What this is not:** merging back into the *invoking* session (D1's rejected approach,
still rejected — the JSONL-corruption risk that motivated D1 is unrelated to this and
still applies). This resumes the *browser session's own* transcript, sequentially, in a
different terminal — the same session, not two sessions merged.

**Why not automatic on tab-close:** a closed WebSocket doesn't distinguish "the user is
done and wants to switch to a terminal" from "accidental close" or "network blip" — the
existing reconnect-on-disconnect behavior (`open-gui-chat`) already depends on
disconnects being non-terminal by default. Auto-triggering a hand-off on disconnect would
regress that. The hand-off is therefore always an explicit, separate action: stop the
session, then the user runs `claude --resume <id>` themselves. See
`open-gui-session`'s "Deterministic claude session id for manual hand-off" requirement
and `SKILL.md`'s "Switch to a normal terminal" section.

**Revision (2026-08-07): confirmed unchanged under D11.** The Agent SDK's `query()`
options include `sessionId` (must be a UUID; its own type declaration documents it as
"resumable via `query({ options: { resume: sessionId } })`" — the SDK-level mirror of the
CLI's `--session-id`/`--resume` pair this decision already relies on). Verified live in
the D11 spike (`system/init`'s `session_id` matched what was passed in). No change to this
decision's requirement or `SKILL.md`'s hand-off instructions — only the spawn mechanism
underneath changed.

### D11: Agent SDK (`canUseTool` + streaming input) replaces the PTY entirely

**Context:** raised by the user directly ("我們沒辦法直接攔截 claude output 來處理嗎"),
asked three times across this session before being investigated properly. The first two
times, the answer given was D4's transcript-inference rejection — correct as far as it
went, but answering a bigger question than was asked. The actual answer needed one
targeted fact: does anything let a caller intercept *just* `AskUserQuestion`, structured,
without reconstructing the rest of the session from output? Direct research (not assumed)
found yes — the Agent SDK's `canUseTool` callback.

**Mechanism (verified live via a Deno spike, not assumed from docs alone):**
- The backend drives each session via `@anthropic-ai/claude-agent-sdk`'s `query()`,
  imported directly under Deno through an `npm:` specifier — no separate Node.js process.
  The package resolves to pure ESM with no runtime dependencies of its own and an
  `engines.node >= 18` floor; it spawns the real `claude` CLI binary as a subprocess
  itself (same binary this design already relies on elsewhere), so `open-gui`'s Deno
  process needs `--allow-run` for it.
- Input is a streaming async generator of user messages (not a single string prompt) —
  this is what keeps the session open indefinitely for a long-lived browser-driven
  conversation rather than the one-shot examples in the SDK's own docs.
- A `canUseTool` callback is passed in `query()`'s options. For `toolName ===
  "AskUserQuestion"`, the callback receives the exact `questions` array structure this
  doc's `question` node type already mirrors (`question`, `header`, `options[]` with
  `label`/`description`, `multiSelect`) — and *blocks* until the callback resolves.
  **Verified live:** the spike held this callback pending for 20 real seconds (simulating
  a user actually reading and thinking) with no timeout, no dropped connection, and a
  `rate_limit_event` message arriving mid-wait confirmed the underlying stream was live,
  not frozen. After answering, the session correctly continued (`result` message,
  `stop_reason: "end_turn"`).
- The backend resolves that pending callback from a WebSocket message the browser sends
  when the user picks an option — keyed by the specific tool-use id, so there is no
  "which node is currently live" ambiguity of any kind (D5's unfixed risk). Other tools
  (`Write`, `Edit`, `Bash`, etc.) also flow through `canUseTool`; default policy is
  auto-approve everything except `AskUserQuestion`, matching this project's existing
  "Claude works autonomously, the human is only needed for genuine judgment calls"
  philosophy (D8/D9) rather than reintroducing a permission-prompt UI this design never
  asked for.
- **Terminal panel → transcript pane, not a rebuilt chat UI.** The temptation here is to
  also hand-build a full chat interface (streaming text, tool cards, diffs) now that
  there's structured data to render — resist it. The bugs this session came from *input*
  (D5's keystroke protocol) and *staleness* (D4/D5's lag), not from rendering Claude's
  output, which xterm.js was never broken at. The replacement panel renders the SDK
  message stream as plain formatted text (assistant text, one-line tool-call summaries) —
  a scrolling list, no ANSI/xterm dependency, minimal new surface area. A richer chat UI
  is a future, separately-scoped change if actually requested, not a default that rides
  along with this pivot.
- `TREE.json`'s role narrows accordingly (see D4's revision, D9): `decision`/`artifact`/
  `info` nodes only for `grill-with-web`. The `question` node type stays in `open-gui`'s
  schema for other consumers, but nothing in `grill-with-web`'s flow writes one anymore —
  the tree panel's auto-advance/frontier-guessing logic (`findFrontierId`,
  `open-gui-tree`'s "auto-advance" scenarios) is removed outright, not patched again: it
  existed only to guess at "the currently live question," and there is no longer a
  currently-live question for the tree to track at all.

**Alternatives considered:**
- **Full transcript/PTY-output reconstruction of the tree** (the literal reading of "攔截
  output"): rejected, unchanged from D4 — no stable contract to parse, still fragile.
  This is *not* what D11 does; the distinction (narrow structured signal via SDK vs. full
  output parsing) was the deciding factor once actually researched.
- **Keep the PTY, add a "menu is currently showing" detector** (a narrower patch discussed
  before this decision, using the raw-mode menu's fixed footer text as a presence signal):
  superseded — once the SDK's `canUseTool` was confirmed to deliver the same information
  structured and pre-parsed, detecting a rendered menu's *existence* became strictly worse
  than receiving its *content* directly.

**Consequence:** this obsoletes D2 (PTY), D3's Node sidecar, and D5 (keystroke protocol)
in one pivot — a full rewrite of `open-gui`'s `server/` and the terminal-rendering half of
`web/`, not an incremental patch. Accepted: the bug category this session spent the most
time on (staleness, duplicate rendering, keystroke fragility) is structurally eliminated
by the pivot rather than chased with another heuristic, which is the whole reason it was
worth the rewrite cost. `tasks.md` tracks the new implementation tasks separately from the
superseded PTY-era ones (marked, not deleted, per this file's existing practice of keeping
the record of what was tried).

### D12: Node-graph canvas replaces the split-view (chat panel + tree spine/detail)

**Context:** live use of D11's split-view surfaced concrete complaints: text too small/
low contrast, the two panels showing overlapping information in an unintuitive way
(a resolved question's answer only visible in the detail pane, not alongside the
question itself), and no sense of the discussion's own topic or of which reply was about
which node. User's proposed replacement: a single top-down node-graph canvas as the
primary view (a `TreeSpine`/`NodeDetail`-style master/detail pair no longer exists at
all), chat as a node type rather than a separate panel, ask+answer unified on one card,
and Claude's replies routed to the node they discuss via an explicit tag.

**Contrast/size fix, shipped first and independently:** `--dim` was ~3:1 against `--bg`
in both palettes (below WCAG AA's 4.5:1 for normal text) — lightened to `#8a948d`
(dark)/`#525d54` (light). Base font size raised from 13px to 15px. This part didn't wait
on the canvas redesign since it's a token-level fix with no design decision attached.

**Mechanism:**
- `@xyflow/react` (MIT, pure-ESM-compatible, `react`/`react-dom` peer `>=17`) renders the
  canvas; `@dagrejs/dagre` (the maintained fork — plain `dagre` is unmaintained) computes
  a top-down (`rankdir: "TB"`) layout from the same parent/child relationships `TREE.json`
  already carries. Verified via each package's own npm registry metadata before adding
  the dependency (per this project's own "look up current docs, don't assume" rule).
- A synthetic root card — not a `TREE.json` node — is always node #1, carrying the
  session's `topic` (user: "討論主旨應該是第一張節點"). Every `decision`/`artifact`/`info`/
  `question` node in `TREE.json` becomes its own card, laid out beneath it.
- **`#[id]`-tagged routing** (user-proposed, reliability-checked live before building
  any routing logic — a 1-round Deno smoke test confirmed the seed-prompt instruction is
  followed correctly: a tagged reply came back exactly as `#[node-id] ...`, an unrelated
  closing remark came back with no tag at all): a leading `#[node-id]` on an assistant
  message routes it into that node's own card, appended to a thread rendered beneath its
  ask/answer content — "把 ask 和 answer 放恣同一張卡片上", extended to "and the
  follow-up discussion goes right below that, same card." Anything untagged, or tagged
  with an id that isn't a real current node, renders on the root card's thread instead —
  user-specified twice: only a *leading* tag counts ("只有開頭的明確要帶的，才是要接"),
  and a non-matching tag is left as plain text, not swallowed ("不要過度敏感 #slug 如果
  對不到的，代表那可能是真的 #slug 要送給使用者") — `lib/tagRouting.js` implements both
  guards. The tag itself is stripped from what's displayed once it does route somewhere.
  The same routing rule applies once to a live `AskUserQuestion` call's first question
  text, so a question can also land on the node it's actually about instead of always
  defaulting to root.
- Tool-use activity (`Bash`, `Read`, etc.) has no natural place for Claude to embed a tag
  (the tool's `input` isn't freeform text), so it always renders on the root card's
  thread — user-chosen explicitly over hiding it, so exploration stays visible/legible.
- Every card has a **fixed footprint** (340×220px, `lib/layout.js`'s `CARD_WIDTH`/
  `CARD_HEIGHT`) with its own internally-scrolling thread, so dagre's layout input never
  changes shape as a thread grows — deliberately traded away free-form manual dragging
  for v1 (`nodesDraggable={false}`) rather than building the drag-position-preservation
  logic a controlled, auto-relaying canvas needs to combine with manual repositioning;
  the user's actual ask was top-down auto-layout, not manual arrangement.
- **AutoPan** (user: "新訊息來記得要 scroll canvas" — a canvas has no linear "bottom" to
  scroll to the way the old transcript pane did): the viewport centers on whichever
  card's thread just grew, or on the node a new live question routed to, via React
  Flow's own `setCenter`.

**Program-driven TREE.json mutation, narrowly scoped (user-proposed):** D4's "Claude is
the sole author of `TREE.json`" is not reversed, but gets one deliberate, narrow
exception — reconsidering a resolved node. Previously (D11) this only ever sent Claude a
message and waited a full turn before the node's `status` changed at all. Now the backend
flips that one node's `status` back to `open` directly — an atomic read-modify-write,
`state.ts`'s `patchNodeStatus` — for instant UI feedback, and *separately* still sends
Claude a message so the cascade reasoning (what else depended on this node) still gets
real judgment, not a mechanical guess. This is safe specifically because it's narrow (one
field, one node, a structural flip) and because the content authoring — resolution text,
new nodes, cascade updates — still only ever comes from Claude. Not locked against a
concurrent write from Claude's own process; accepted as a rare, low-stakes race (see
`state.ts`'s comment on `patchNodeStatus`).

**Two new explicit session controls, both browser-triggered:** a "定案" (finalize)
button sends Claude a direct instruction to wrap up now, without waiting for Claude to
decide to call `AskUserQuestion` itself first (`session:finalize`). A "Stop" button lets
the browser request shutdown directly (`session:stop`) rather than requiring an external
`SIGTERM`. Both are explicit user actions, not inferred task-completion — the same
category as D8/D9's two "mechanical" exceptions to "never shut down," not a reversal of
that rule (an inferred-completion auto-close is still never done; a user clicking a
button that says "stop" is not an inference).

**Consequence:** this deletes `TreeSpine.js`, `NodeDetail.js`, `TranscriptPane.js`,
`SplitView.js`, and the master/detail model entirely — a second full frontend rewrite
within hours of D11's, on top of an already-large session. Accepted: each complaint this
addresses (contrast, duplicate/unintuitive display, no sense of topic or of which reply
answers what) was concrete and reproducible in the shipped D11 UI, not a hypothetical
improvement — and the `#[id]` mechanism was reliability-checked live before any routing
logic was built on top of it, rather than assumed.

**Revision (2026-08-07): five rounds of live-testing fixes on the first canvas build.**

- **Critical: no card was interactive at all.** Every button/input inside a custom React
  Flow node was silently eating clicks and refusing focus. Root cause (confirmed against
  React Flow's own docs, not guessed): the canvas's own pan handler captures pointer
  events inside custom nodes by default; interactive elements need the library's `nopan`/
  `nodrag` convention classes to opt out. Every button, input, and textarea across every
  card, `Thread`, `LiveQuestionCard`, and `FreeTextBox` now carries them
  (`lib/cn.js` added — a minimal classname joiner, this project has no Tailwind so no
  `tailwind-merge` is needed, just safe conditional joining — after a user correction
  ("tailwind class 要用 cn 合併才能這樣寫") pointed at manual template-literal
  concatenation as the pattern to fix, even though this project has no Tailwind).
- **Session-level controls moved out of the canvas entirely** (user: "root 的選項和輸入
  可能要拉到 canvas 外面的 layout，定案 or stop or 收斂都應該放到 navbar，message 應該放
  到最外層的 chat"). `Navbar.js` (topic, status, theme toggle, 定案/Stop) and `ChatBar.js`
  (the general message input) are fixed chrome siblings of `<ReactFlow>`, not nodes
  inside it — reachable regardless of pan/zoom position. The root card lost its own
  footer entirely; it's now shaped like any other card (a thread, nothing else).
- **Cards switched from a fixed pixel height to CSS min/max-height** (user: "卡片的高度不
  能固定，這樣內容都看不清楚" — the original fixed 220px genuinely clipped real
  recommendation/resolution text). `lib/layout.js`'s `CARD_HEIGHT` is now explicitly
  documented as a dagre spacing *estimate*, not a promise the rendered card matches it —
  safe because dagre only needs a number to avoid overlapping rows, not pixel-perfect
  agreement with final CSS height.
- **Cards show only their latest entry; DetailSidebar shows the rest** (user: "card 顯示
  最後的回應，但是 focus card 的時候，可以用邊欄 layout 顯示那一段的完整過程"). New
  `DetailSidebar.js`, docked on the right, renders the focused card's full thread — and,
  when that card has a live pending question, the actual interactive `LiveQuestionCard`
  UI too (moved out of the cramped fixed-width card entirely, after the user noticed a
  question's options weren't visibly rendering in the small card: "問題選項沒有出來，是
  不是 focus 的時候可以顯示再卡片旁邊"). Promote-to-tree ("加進 tree") was removed
  outright at the same time — the user judged it no longer needed once `#[id]`-tagged
  routing already places discussion on the right card without a manual step.
- **Click-to-focus and keyboard navigation**, sharing one `activeNodeId`/`manualFocusId`
  concept with AutoPan: clicking a card, or `Tab`/`Shift+Tab`, cycles focus among cards
  that need action (a live pending question, or an open `question`-type node) and pans
  the viewport there. Within the focused card/sidebar: digit keys `1`-`4` pick-and-submit
  an option (single-question calls only — a multi-question call has no unambiguous "the"
  option list for a bare digit, so it's mouse-only there, a documented simplification);
  `/` focuses the card's own reply/Other input; `n` focuses its notes field where one
  exists; `:` always focuses the global `ChatBar`, regardless of what's focused on
  canvas. An explicit click/Tab wins over auto-drift (so looking around doesn't fight the
  user), but a genuinely *new* question still reclaims focus even from a manual look-away
  — tracked by clearing `manualFocusId` on a new `requestId`, not on every render.
- **`#[id]` tagging broke under real interview conditions, not just the isolated
  reliability check.** Live testing surfaced Claude tagging a reply `#trim` — no
  brackets, and abbreviated from the real id `trim-whitespace` — which silently fell
  through to the root card exactly as designed (no false match), but defeated the whole
  point (user: "我發現問題選項都跑到 root 去了，應該放到對應的 card 去"). The single-
  round tagcheck (D12's first revision) wasn't representative of a full multi-turn
  interview's instruction-following. Fixed at the prompt, not by loosening the matching
  rule — `grill-with-web/SKILL.md` now spells out "copied verbatim, character for
  character" with a worked example and an explicit warning against tagging from memory,
  deliberately not adding fuzzy/prefix matching on the frontend (which the user had
  already ruled out earlier: "不要過度敏感"). Re-verified live after the prompt fix: a
  3-question `AskUserQuestion` call correctly used `#[trim-whitespace]` and
  `#[capitalize-first-letter]` verbatim, routed correctly, and reached `status: complete`
  with a well-formed summary doc. Separately fixed a real display bug found in the same
  session: only the first question's tag was ever stripped for display (routing is
  decided from it alone), so a second/third tagged question in the same call showed raw
  `#[id]` syntax to the user — `lib/tagRouting.js`'s `routeQuestion` now strips every
  question's own leading tag for display while still deciding routing from the first
  question only.

**Revision (2026-08-07): follow-up discussion chains downward as ephemeral cards, not
one card accumulating a thread.** Live use of "重新考慮" surfaced the gap directly: the
agent's post-reconsideration analysis didn't carry the reconsidered node's tag, so it fell
back to the root card by design (per the tag-routing rule above) — but for a user watching
a specific node get re-litigated, seeing that reasoning land on root, mixed in with
everything else, reads as broken continuity, not "correctly untagged." One card silently
absorbing every reply into a `Thread`/`limit={1}` preview + DetailSidebar-on-focus doesn't
communicate "this is round 2 of the same discussion" the way a visibly separate card,
chained below the first, does.

**Considered and rejected: have the agent write real child `decision` nodes into
`TREE.json` for each round of follow-up.** This was the first framing put to the user, who
initially picked it — but it fails a straightforward cost check against what's actually
needed: `NODE-FORMAT.md` scopes `TREE.json` to decisions/artifacts/info/questions, not
conversational back-and-forth, and persisting every round would need new schema, new
`grill-with-web/SKILL.md` instructions, and backend tree-traversal to compute an
attachment point — all to solve what is, underneath, a rendering problem. Superseded below.

**Decision: chain ephemeral canvas cards, `TREE.json` untouched.** Reuses the pattern
D12 already ships for live `AskUserQuestion` cards — a React Flow node synthesized from
data the frontend already has, with an edge to a parent, but never written to
`TREE.json`. Each subsequent tagged reply to an already-resolved-once node's branch
becomes its own card chained below the previous one, instead of folding into that node's
`Thread`. `TREE.json` gains a node only when the agent, as always, judges the round has
actually reached a new decision worth persisting — content-authoring stays entirely
Claude's call, unchanged from D4. **This is not a D4 reversal**: D4 rejected inferring
structure from unstructured transcript/PTY prose; deciding which already-tag-routed
thread entry chains under which card is a pure function over structured data the frontend
already computes (`threadsByTarget`, the same `#[id]` routing D12 already relies on) — the
same category as D12's existing narrow `patchNodeStatus` exception, not the alternative
D4 rejected.

**Attachment rule: most recently active node in the branch, not "deepest."** Computing a
true deepest-open-descendant would need actual tree traversal; the existing
`lastEntryTarget` tracking (CanvasView.js — which card's thread grew most recently)
already answers "where is this branch's discussion right now" without it. Generalizes
per-branch: when a new tagged reply lands, it chains under whichever card in that node's
branch most recently received an entry, defaulting to the tagged node itself if the
branch has no chained cards yet.

**No cap on chain length.** A single branch could in principle grow to ten-plus rounds
(~3,500px at current `CARD_HEIGHT`/`ranksep`) — accepted rather than building
collapse/expand UI for it, since AutoPan already centers the viewport on whatever card
most recently grew and React Flow's own pan/zoom handles the rest. Revisit only if this
proves to be a real problem in practice, not preemptively.

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
- **[Risk] Target session has no way to discover its own `TREE.json` path** — realized
  while preparing Task 9.3 (`grill-with-web` end-to-end, previously unrun): the spawned
  `claude` process's own `--session-id` (`claudeSessionId`) is a *different* id from the
  Deno-level `session-id` that determines the state directory, and that path is never
  passed as an env var. A calling skill that builds a seed prompt following only
  `NODE-FORMAT.md`'s schema (without also embedding the literal absolute `TREE.json`
  path) would spawn a session with nowhere to write it — the live tree would silently
  never populate.
  → **Fixed**: `open-gui/SKILL.md`'s "For other skills invoking open-gui" section now
  spells out that the calling skill chooses `session-id` itself specifically so this path
  is computable before launch, and must include the literal path in the seed prompt, not
  just a schema reference. `grill-with-web/SKILL.md` step 1 updated to match.
- **[Risk] `open-gui`'s fully-passive lifecycle (D8) means a forgotten standalone session
  leaks a running `claude` process + backend indefinitely** if the user never closes it.
  → **Mitigation, updated 2026-08-07**: originally accepted as-is ("document how to stop
  manually, `grill-with-web` is the one consumer that auto-shuts-down"). User-raised from
  real usage (accidentally closing a tab, worried about accumulation across repeated
  sessions) that "manual only" wasn't good enough even for standalone `open-gui`. Now
  mitigated automatically too — see D8's idle-shutdown/`session:ended` revision above —
  without reintroducing task-completion inference.
- **[Risk] A fresh target session spends its own first turn on avoidable discovery**
  (invoking the `Skill` tool for `grill-with-docs`, hunting for `NODE-FORMAT.md` —
  observed: 30s+ and a failed background search) when the seed prompt only *references*
  skills/files by name/path instead of containing what they say. User-raised from real
  usage ("重新檢討這個流程設計" — after watching `grillweb5` burn a turn loading a skill
  and locating a doc that the calling skill already had `Read` access to).
  → **Fixed**: `open-gui/SKILL.md`'s "For other skills invoking open-gui" and
  `grill-with-web/SKILL.md` step 1 now both say explicitly: the calling skill reads
  `NODE-FORMAT.md` (and, for `grill-with-web`, `grill-with-docs`'s own instructions)
  itself and writes their actual content into the seed prompt — never just a path or
  skill name for the target session to go resolve on its own turn one.

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

- ~~**Timeout value for the invoking session's completion poll**~~ — resolved during
  implementation: 10 minutes per poll attempt, checking every ~5s. Chosen to fit inside
  a single Bash tool call's own execution ceiling (the invoking session is a
  conversational agent turn, not a true background process — it cannot block
  indefinitely within one tool call). On timeout, `grill-with-web`'s SKILL.md reports
  "still running" rather than waiting silently; the user can ask again, which re-polls
  the same state directory rather than starting a second session. See
  `skills/grill-with-web/SKILL.md` step 3.

- **Seed-prompt delivery timing against a real `claude` TUI — partially resolved
  (2026-08-07), root cause found for the "sat visibly un-submitted" symptom below.**
  Running Task 9.3 for real (previously never run) reproduced it directly: the seed
  landed in the input box collapsed into a `[Pasted text #1 +1 lines]` chip and never
  submitted. Root cause: Claude Code's TUI detects a long single burst of characters
  (the ~1.5KB seed prompt, written to the PTY in one shot) as a paste and buffers it into
  that placeholder; the trailing `\r`, sent in the *same* write, gets absorbed into the
  paste-detection event instead of registering as a separate "submit" keystroke — a
  distinct failure mode from the multi-line/embedded-newline bug fixed earlier (below).
  **Fixed**: `scheduleSeedSend` in `main.ts` now writes the seed text and the submitting
  `\r` as two separate writes, 200ms apart, so the `\r` arrives after the paste-detection
  window has closed. Verified live: the seed now submits and the target session starts
  working immediately. **Still open**: this run did not encounter a first-run gate screen
  (the welcome banner read "Welcome back Wei!", implying trust was already established
  for this user/environment) — the broader risk below, of an *unpredictable* one-time
  gate racing the seed regardless of the paste-detection fix, remains untested and
  unresolved.

- Manual testing (2026-08-07) against the real `claude` binary (not the bash
  stand-in used for earlier protocol verification) found the "wait for first `data`,
  then write" rule (§3 of `PROTOCOL.md`) races an unpredictable number of one-time
  first-run screens — observed both a "trust this folder?" gate and a "try the new
  fullscreen renderer?" opt-in, on different runs, neither of which is something
  `open-gui` can enumerate in advance. Across four runs the seed prompt variously: typed
  itself into the trust dialog (harmless — the trailing `\r` happened to confirm the
  already-defaulted option), sat visibly un-submitted in the real chat input (multi-line
  compose vs. submit ambiguity, since fixed separately — see below), and landed
  invisibly with no observable effect at all (most likely consumed by a gate screen
  during its own transitional state). No fix was found within scope — pattern-matching
  Claude Code's specific TUI output to detect true input-readiness was rejected as
  contradicting D4's own "don't infer structure from PTY output" principle, applied here
  by extension. **Consequence:** `grill-with-web` (the one caller that depends on seed
  delivery) may need the target project pre-approved (trust dialog already dismissed
  once, e.g. by a prior manual `claude` run) to be reliable; this is a real, undismissed
  limitation, not merely a hypothetical edge case, and Task 8.1 does not fully close it.
  Two bugs found *during* this investigation were real and got fixed regardless of the
  above: (1) a seed prompt containing an embedded/trailing newline landed in the input
  box but never submitted, because a raw PTY treats an embedded `\n` as "insert a line,"
  not "submit" — fixed by collapsing the seed prompt to one logical line before
  appending the terminal `\r` (`main.ts`); (2) the spawned `claude` process inherited
  this harness's own `CLAUDE_CODE_CHILD_SESSION` marker via `Deno.env.toObject()`,
  directly contradicting D1's "brand-new, independent session" — the spawned session
  reported transcript saving disabled as a result. Fixed by filtering all
  `CLAUDE`-prefixed env vars out of the spawn environment (`independentSpawnEnv()` in
  `main.ts`) rather than passing the harness's environment through wholesale.

- **Reconnecting to a live real-`claude` session (alt-screen buffer replay) — still
  untested.** `pty:snapshot` replays raw buffered scrollback bytes into a fresh xterm
  instance (see `PROTOCOL.md` §2); this was verified against the `/bin/bash` stand-in
  (Task 3.9) but never against a real `claude` TUI, which uses the alternate screen
  buffer. Closing and reopening a live real-`claude` session's tab is the specific
  scenario that would surface any corruption here. Flagged, not yet exercised.

Two more real bugs surfaced and were fixed in this same pass (both only reproduce
against a real `claude` TUI or fast real typing — the `/bin/bash`-based Task 3.9/4.x
verification never exercised either path):

- **Fast keystrokes could be silently dropped.** `sidecar_client.ts`'s `#send()`
  acquired a fresh `getWriter()`/`releaseLock()` pair per IPC message; overlapping
  `pty:write` messages (e.g. fast typing, each keystroke its own WS message) raced for
  the lock and threw `TypeError: The stream is already locked`, dropping that
  keystroke — the failure was silent to the user (caught and logged server-side only).
  Fixed by acquiring one writer for the connection's lifetime instead of per call.
- **`TREE.json` writes via atomic write-then-rename never triggered a live push.**
  `Deno.watchFs`'s event filter only accepted `modify`/`create`; confirmed (via a
  throwaway watcher script) that an atomic writer — including Claude Code's own `Write`
  tool — produces a `rename` event on the final path instead, which the filter silently
  dropped. The browser's tree panel would show stale/empty state indefinitely with no
  error. Fixed by accepting `rename` alongside `modify`/`create`.
- ~~**Exact IPC message shape between the Deno process and the Node sidecar**~~ —
  resolved: newline-delimited JSON over a TCP loopback socket (`PROTOCOL.md` §1), message
  types `spawn`/`write`/`resize` (Deno → sidecar) and `spawned`/`data`/`exit`/`error`
  (sidecar → Deno).
- **Windows support is unverified end-to-end.** The confirmed-necessary fix (TCP loopback
  instead of Unix domain socket, since Deno has no Windows support for the latter) is
  done, and `node-pty` itself supports Windows via ConPTY (a separate native binding,
  already present in the resolved package — no code change needed there). Cross-platform
  gaps addressed opportunistically while investigating (`HOME`/`USERPROFILE` fallback in
  `state.ts`, path-separator handling in `projectSlug()`) are best-effort, not verified —
  this machine has no Windows environment to test against. Still open/unverified:
  `Deno.watchFs` event-kind behavior on Windows (the `rename`-vs-`modify` finding above
  was macOS-specific; Windows may differ again), and the sidecar's
  `fix-spawn-helper-permissions.js` postinstall step (a no-op on Windows since it only
  touches Unix-specific paths that won't exist — should be harmless, not exercised).
