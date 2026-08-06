# grill-with-web — Design

## Purpose

`grill-with-web` extends `grill-with-docs` with a live, browser-based front end. The
grilling interview still runs as a real, interactive `claude` CLI session — the point
is that the *entire* conversation can happen in the browser instead of the terminal,
with a node-based decision tree rendered alongside it so the user's mental model stays
visibly aligned with the agent's as branches resolve. Unless the user explicitly steps
out of the GUI, nothing about finishing the grill requires going back to a terminal —
only the resulting documents (CONTEXT.md, ADRs, tree summary) need to flow back into
the original working session.

This is not a new interview format. `grill-with-web` provisions infrastructure and a
seed prompt, then hands the actual interview off to `grill-with-docs` running inside a
freshly spawned session. All of `grill-with-docs`'s document-writing behavior (CONTEXT.md
glossary, sparing ADRs) is reused unmodified.

## Prior art

Researched before designing: [siteboon/claudecodeui](https://github.com/siteboon/claudecodeui)
and [vultuk/claude-code-web](https://github.com/vultuk/claude-code-web) both PTY-wrap a
`claude` subprocess with `node-pty` + xterm.js over WebSocket. [sugyan/claude-code-webui](https://github.com/sugyan/claude-code-webui)
instead drives the Claude Agent SDK's `query()` headlessly and streams NDJSON. No
surveyed project uses Next.js — all use a separate persistent Node/Deno process for the
PTY/WebSocket layer, since long-lived PTY streaming doesn't fit Next.js's API Route
lifecycle. This design follows the PTY + xterm.js family (full CLI fidelity, including
permission prompts) with Next.js used purely as a static frontend build tool.

## Session model: always a fresh session

The obvious design — resume/continue the session the user is already in, so the web
session inherits full conversation history — was rejected. Anthropic's own issue tracker
documents unresolved, "not planned" data-corruption risk when a session's JSONL
transcript is touched by more than one `claude --resume`/`--continue` process:
conversation-tree forking from concurrent writes ([#48270](https://github.com/anthropics/claude-code/issues/48270)),
parentUuid chain corruption on resume ([#36583](https://github.com/anthropics/claude-code/issues/36583)),
and silent writer failure after a CLI upgrade ([#53417](https://github.com/anthropics/claude-code/issues/53417)).
None of this is under this skill's control.

`grill-with-web` therefore always starts a **brand-new, independent session** — no
`--resume`, no `--continue`. Whatever background the web session needs is written
directly into its seed prompt (topic, relevant file paths) rather than inherited via
transcript. This has a second-order benefit: because the two sessions never touch the
same transcript file, there is no risk from the user also typing in the original
terminal session while the web session is running — that failure class is eliminated
entirely, not just mitigated by asking the user not to.

The trade-off is explicit: the web session doesn't have the original session's full
chat history. Only the original session's stated topic/background and the final written
documents bridge the two — which is exactly what the user asked for ("最後結果才需要
回到 Claude Code 裡面").

## Architecture

```
Original terminal session (this one)
   │  1. computes state dir, builds seed prompt
   │  2. starts backend, opens browser
   ▼
skills/grill-with-web/SKILL.md  ──spawns──▶  Deno backend (single process)
                                                 │
                                    ┌────────────┼─────────────────┐
                                    │            │                 │
                              node-pty      Deno.serve()      watches
                              spawns a      serves Next.js    TREE.json
                              *fresh*       static export     for changes
                              `claude`      + WebSocket
                              process       (PTY I/O +
                              (new          tree events +
                              session id)   doc-preview
                                            requests)
                                                 │
                                                 ▼
                                     Browser (Next.js static page)
                                     ┌─────────────┬────────────────┐
                                     │  xterm.js   │  Tree panel    │
                                     │  terminal   │  (live nodes,  │
                                     │  (full PTY  │  per-node      │
                                     │  fidelity)  │  input, doc    │
                                     │             │  preview)      │
                                     └─────────────┴────────────────┘
   ▲
   │  4. polls TREE.json top-level `status` for "complete"
   │  5. kills Deno process, reports artifact paths
   └─ back to the user, here, once done
```

One Deno process handles both the PTY-wrapped `claude` subprocess and all HTTP/WebSocket
serving — no separate frontend server. `node-pty` runs under Deno's npm compatibility
layer; this requires `node-pty@1.1.0-beta37` or later (older versions crash under Deno —
[denoland/deno#31032](https://github.com/denoland/deno/issues/31032)) paired with a recent
stable Deno release. This compatibility path is new; verify it in the target environment
before relying on it, with a Node.js PTY sidecar as the documented fallback if it proves
unstable.

## Components

```
skills/grill-with-web/
  SKILL.md            # orchestrator: state dir, seed prompt, start/stop, completion poll
  NODE-FORMAT.md       # TREE.json schema (sibling to grill-with-docs's *-FORMAT.md files)
  server/
    main.ts            # Deno entrypoint: node-pty spawn + Deno.serve (static + WS)
    deno.json           # declares npm:node-pty dependency
  web/                  # Next.js project, `output: 'export'` — build tool only,
                         # no Next.js runtime server involved
```

Runtime state (not committed, lives outside the target project repo):

```
~/.claude/state/<project-slug>/grill-web/<new-session-id>/
  TREE.json
```

Deliverables (written into the **target project's** repo, by the web-session Claude,
following existing `grill-with-docs` conventions):

```
CONTEXT.md                      # unchanged grill-with-docs behavior
docs/adr/000N-slug.md            # unchanged grill-with-docs behavior, offered sparingly
docs/grill/<slug>.md             # new: Mermaid diagram generated from TREE.json + summary
```

## TREE.json

Defined in `NODE-FORMAT.md`. Written incrementally by the web-session Claude the moment
each branch resolves — same "capture it when it crystallizes" discipline `grill-with-docs`
already uses for CONTEXT.md.

```json
{
  "topic": "API 版本策略",
  "status": "in_progress",
  "nodes": [
    {
      "id": "n1",
      "parent": null,
      "question": "Bump major，還是用 header versioning？",
      "recommendation": "Header versioning — client 不用改 URL",
      "status": "resolved",
      "resolution": "採用 header versioning",
      "adr": "docs/adr/0003-header-versioning.md"
    },
    {
      "id": "n2",
      "parent": "n1",
      "question": "Deprecation 期限多長？",
      "recommendation": "6 個月",
      "status": "open"
    }
  ]
}
```

- Top-level `status` (`in_progress` / `complete`) is the completion signal the
  orchestrating skill polls for.
- `resolution` is present only on `resolved` nodes.
- `adr` is optional — only set when that specific decision produced an ADR (`grill-with-docs`
  offers ADRs sparingly, not for every resolved node). It's what lets the tree panel's
  doc-preview open the right file.
- No timestamps, no verbatim transcript quotes — neither the live tree render nor the
  final summary doc needs them.

## GUI

**Layout:** split view — xterm.js terminal (left, ~60%) and tree panel (right, ~40%),
divider is draggable. Both panels stay visible at all times; this was chosen over a
terminal-primary+collapsible-tree layout and a tree-primary+console-drawer layout because
ambient, continuous visibility of the tree is the actual point of this skill — collapsing
it by default would undercut that.

**Visual theme:** "作戰室" (op-sec minimal) — pure near-black background, a single cool
green accent, no CRT glow or scanlines, thin 1px borders, monospace throughout, high
information density. Modeled on modern security-tooling aesthetics (Burp Suite, tmux)
rather than retro CRT — deliberately fixed/single-theme regardless of the viewer's
light/dark preference, since it's a committed visual world for this tool specifically.
Tokens approved during design: background `#0a0c0b`, panel `#101211`, border `#242825`,
foreground text `#d7ddd4`, dim/secondary text `#5c655e`, accent `#9dff5c`, monospace
throughout, no glow/text-shadow.

**Terminal panel:** full-fidelity PTY-wrapped `claude` CLI — permission prompts, tool
use, slash commands, everything renders exactly as it would in a real terminal. This
panel is the single source of truth for the conversation.

**Tree panel interactions:**
- Each node has a small input box. Text typed there is sent to the *same* PTY stdin as
  the terminal panel — it is a convenience entry point, not a parallel conversation. The
  terminal always echoes it, so there is exactly one conversation thread regardless of
  which panel the user types in. Submitting from a resolved node's box prefixes the text
  with a reference to that node's question, so a follow-up like "actually, what about
  mobile clients?" carries its context into the single linear stream.
- Clicking a `resolved` node with an `adr` link opens a slide-over panel rendering that
  file's markdown (read-only preview, not editable in-GUI). Backed by a small Deno
  endpoint that reads the file and returns its contents; the frontend renders it client-side.

## Session lifecycle

1. Original session computes the state dir, builds the seed prompt (topic + background +
   relevant file paths — see below), starts the Deno backend.
2. Backend spawns a fresh, independent `claude` process via `node-pty` (new session id,
   cwd = target project), feeds the seed prompt as its first input, and starts serving
   the frontend + WebSocket, binding to port 0 (OS-assigned, avoids conflicts).
3. Original session opens the browser to the server URL. Auto-open is attempted but not
   guaranteed (confirmed unreliable under WSL without extra tooling); the URL is always
   printed as a fallback — WSL2's localhost port-forwarding to the Windows side works
   regardless of whether the browser auto-launches.
4. Original session blocks, polling TREE.json's top-level `status` for `complete` (with
   a timeout). The user can also cancel directly by telling the orchestrating Claude to
   stop, which kills the Deno process without waiting for the signal.
5. All interaction happens in the browser. As nodes resolve, TREE.json updates and the
   backend pushes the change over the same WebSocket used for PTY I/O.
6. Closing the browser tab does not end the session — the PTY process stays alive
   server-side; reopening the URL reconnects to the same live session.
7. When the web-session Claude reaches shared understanding, it writes CONTEXT.md/ADRs
   (via `grill-with-docs`) and `docs/grill/<slug>.md` (Mermaid diagram + summary from
   TREE.json), then sets TREE.json's top-level `status` to `complete`.
8. The original session detects this, kills the Deno process, and reports the written
   file paths back to the user — in the terminal session they started from.

## Seed prompt

Built by `SKILL.md`, fed to the freshly spawned session as its first input:

```
執行 grill-with-docs skill，主題：{topic}。
背景：{使用者提供的簡述 + 相關檔案路徑}

額外規則：
- 每當一個問題/分支被 resolved，依 NODE-FORMAT.md 更新 {state_dir}/TREE.json
- 結束時，除了 grill-with-docs 原本的 CONTEXT.md/ADR，
  額外寫一份 docs/grill/{slug}.md（Mermaid 樹狀圖 + 摘要）
- 全部完成後，把 TREE.json 的頂層 status 設成 complete
```

`grill-with-web`'s own `SKILL.md` stays thin: it provisions infrastructure and constructs
this prompt. The interview logic itself remains entirely `grill-with-docs`'s
responsibility — no duplication.

## Error handling

- **`node-pty` fails to build** (missing build tools): fail loudly with a clear message
  naming what's missing. No silent fallback to a degraded mode.
- **Port conflicts:** avoided by binding to port 0 and reading back the OS-assigned port.
- **Browser doesn't auto-open:** always print the full URL; this is the expected path in
  WSL and other remote/headless setups.
- **Browser tab closed mid-session:** not an error — PTY process persists server-side,
  reconnect on reopening the URL.
- **User types in the original terminal session while the web session runs:** not an
  error, not even a risk — the sessions never share a transcript file.

## Testing

Fully automated interactive-tool testing isn't realistic here. Two tiers:

- **Automated (Deno test):** TREE.json schema validation, WebSocket message framing/parsing.
- **Manual smoke test:** start the skill → browser connects → terminal accepts input and
  reflects real `claude` output → tree panel updates live as nodes resolve → clicking a
  resolved node with an ADR link opens the doc preview → typing in a node's input box
  shows up in the terminal → on completion, the Deno process shuts down and the original
  session reports correct file paths.

## Scope

This spec covers `grill-with-web` only. The user noted this "web GUI conversation"
capability could serve any structured discussion, not just grilling. The Deno + PTY +
Next.js infrastructure is written generically enough to extract into a shared primitive
later, but no separate generic skill is designed or built now — YAGNI. If a second
consumer materializes, extract then.
