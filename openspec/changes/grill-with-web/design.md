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
existing reconnect-on-disconnect behavior (`open-gui-terminal`) already depends on
disconnects being non-terminal by default. Auto-triggering a hand-off on disconnect would
regress that. The hand-off is therefore always an explicit, separate action: stop the
session, then the user runs `claude --resume <id>` themselves. See
`open-gui-session`'s "Deterministic claude session id for manual hand-off" requirement
and `SKILL.md`'s "Switch to a normal terminal" section.

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
