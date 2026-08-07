## 1. Environment verification (de-risk first) — done

- [x] 1.1 Verified `npm:node-pty@1.1.0-beta37`+ under Deno: native addon builds and
      `pty.fork()` succeeds, but the read path (`node:tty`'s `tty.ReadStream(fd)`) never
      emits `data`/`exit` events — confirmed with a minimal `/bin/echo` case. Deno-direct
      `node-pty` does not work in this environment (see design.md D3).
- [x] 1.2 Adopted the documented fallback as the primary approach: a Node.js sidecar
      process dedicated to `node-pty`, Deno backend talks to it over local IPC.
- [x] 1.3 Verified `node-pty` works correctly under plain Node.js once a separate,
      non-Deno-specific bug is worked around: the extracted `spawn-helper` binary loses
      its executable bit on this machine under both `deno install` and plain
      `npm install`. `chmod +x` fixes it; confirmed `SMOKE_TEST_PASS` under Node.js
      after the fix. The sidecar's install/startup must defensively re-assert this bit
      (Task 2.1) rather than assuming the package installs it correctly.

## 2. `skills/open-gui/server/sidecar/`: Node.js sidecar (owns the PTY)

- [ ] 2.1 Scaffold `skills/open-gui/server/sidecar/` with a `package.json` declaring
      `node-pty@1.1.0-beta37`+. After install, defensively `chmod +x` any
      `spawn-helper` binaries found under `node_modules/node-pty/{build,prebuilds}/**`
      (Task 1.3 finding) before the sidecar accepts its first spawn request.
- [ ] 2.2 Implement generic PTY spawning: the sidecar accepts a `spawn` IPC message
      (`file`, `args`, `cwd`, `env`, `cols`, `rows`) and forks exactly that — it decides
      nothing about *which* process or seed prompt to use. That policy (fresh `claude`
      process, no `--resume`/`--continue`, seed prompt delivery) lives in the Deno
      backend (Task 3.1) and `open-gui`'s SKILL.md (Task 7.1), not here.
- [ ] 2.3 Implement the sidecar's IPC side: a Unix domain socket accepting
      newline-delimited JSON messages (`spawn`, `write`, `resize`, `data`, `exit`) from
      the Deno process — the exact envelope is fixed in `PROTOCOL.md` (Task 4.1a) before
      either side is coded.
- [ ] 2.4 Fail loudly with a specific, actionable error if `node-pty` fails to build or
      load, or the IPC socket can't be established — no silent degraded mode.

## 3. `skills/open-gui/server/`: Deno backend (serving + sidecar supervision)

- [ ] 3.1 Scaffold `skills/open-gui/server/` with `deno.json`. On startup, spawn and
      supervise the Node.js sidecar (Section 2) as a child process — restart-on-crash
      is out of scope; a sidecar crash SHALL surface as a loud failure (Task 2.4), not a
      silent hang. Owns session-startup policy: sends the sidecar a `spawn` message for
      a fresh, independent `claude` process (new session id, cwd = target project, no
      `--resume`/`--continue`), then writes the seed prompt to its stdin once the PTY
      signals readiness (see `PROTOCOL.md`, Task 4.1a, for the readiness rule — a naive
      immediate write races the TUI mounting, confirmed by the Task 1.3 smoke test
      needing a delay before `p.write` took effect).
- [ ] 3.2 Bind `Deno.serve()` to port 0 (OS-assigned) and read back the actual port.
- [ ] 3.3 Implement the WebSocket endpoint multiplexing three message types: PTY I/O
      bytes (relayed to/from the sidecar over IPC), `TREE.json` change events, and
      doc/artifact-preview file-content requests.
- [ ] 3.4 Forward browser-submitted keystrokes/text (including node interactions from
      the tree panel) to the sidecar over IPC, which writes them to the PTY's stdin.
- [ ] 3.5 Watch the session's `TREE.json` for changes and push updates over the
      WebSocket.
- [ ] 3.6 Implement the doc/artifact-preview request handler: read a given local file
      path under the target project and return its contents (read-only, no write path).
- [ ] 3.7 Ensure the session survives browser disconnects — the sidecar and PTY process
      keep running regardless of WebSocket connection state; reconnecting to the same
      session URL reattaches to the live session.
- [ ] 3.8 Compute the per-session state directory
      (`~/.claude/state/<project-slug>/open-gui/<session-id>/`), write the seed prompt
      and a PID/port record file there before reporting the session URL.
- [ ] 3.9 Prove the full PTY chain end-to-end with a throwaway CLI client (a small
      `deno run` script or `wscat`) before any frontend code exists: connect over WS,
      type into a real spawned `claude` process, see its ANSI output come back. This is
      the checkpoint before Section 5 — if seed-prompt timing or ANSI relay is wrong,
      find out here, not after xterm.js is wired in.

## 4. `TREE.json` schema and wire protocols

- [ ] 4.1a Write `skills/open-gui/PROTOCOL.md` fixing, in writing, before either side is
      coded: the sidecar IPC envelope (newline-delimited JSON; PTY `data` bytes are
      base64-encoded inside the JSON envelope, never embedded raw, since raw PTY output
      contains `\n` constantly and would break line-delimited framing) and the WS
      message envelope (browser↔Deno: PTY I/O, tree-change push, preview
      request/response). Also fixes the seed-prompt readiness rule (Task 3.1) — the
      concrete signal (fixed delay vs. matching an expected startup output pattern) and
      why.
- [ ] 4.1 Write `skills/open-gui/NODE-FORMAT.md` defining the schema: a base node
      (`id`/`type`/`parent`/`title`) plus per-`type` payload for `decision`
      (`recommendation`/`status`/`resolution`/optional `doc`), `question`
      (`prompt`/`options[]`/`status`/`answer`, plus the "Other" free-text and notes
      fields the UI always renders alongside options), `artifact` (local `path`), and
      `info` (`text`).
- [ ] 4.2 Write a Deno test validating `TREE.json` against this schema (structure and
      required-field-per-type-per-status rules).
- [ ] 4.3 Write a Deno test for the WebSocket message framing/parsing (Task 3.3) and the
      sidecar IPC framing (Task 2.3).

## 5. `skills/open-gui/web/`: frontend scaffold and terminal panel

- [ ] 5.1 Scaffold the Next.js project under `skills/open-gui/web/` with
      `output: 'export'` (static build, no Next.js runtime server).
- [ ] 5.2 Integrate xterm.js, wired to the WebSocket for PTY I/O.
- [ ] 5.3 Apply the op-sec visual theme tokens (background `#0a0c0b`, panel `#101211`,
      border `#242825`, foreground `#d7ddd4`, dim `#5c655e`, accent `#9dff5c`,
      monospace, no glow/scanlines), fixed regardless of OS light/dark preference.

## 6. `skills/open-gui/web/`: generic tree panel

- [ ] 6.1 Build the split-view layout: terminal (left, ~60%) and tree panel (right,
      ~40%) with a draggable divider; both panels visible by default, and the tree
      panel renders an empty state (not an error) when `TREE.json` has zero nodes.
- [ ] 6.2 Render the tree from `TREE.json`, updating live as WebSocket push events
      arrive.
- [ ] 6.3 Implement per-type node rendering: `decision` (recommendation/resolution/doc
      link), `info` (text), `artifact` (embed/preview affordance), `question` (prompt +
      option cards) — each visually distinct.
- [ ] 6.4 Implement `question` node interaction: clickable option cards, an "Other"
      free-text field, and a notes field (mirroring `AskUserQuestion`'s interface);
      submitting any of these sends the resulting text to the PTY stdin over the
      WebSocket.
- [ ] 6.5 Implement plain free-text input for other node types where applicable;
      resolved-node submissions prefix the text with a reference to that node's
      title/prompt.
- [ ] 6.6 Add the document/artifact preview: clicking a `decision` node with a `doc`
      field, or an `artifact` node, requests and renders that file's content in a
      read-only slide-over panel.

## 7. `skills/open-gui/SKILL.md`: independent, passive orchestration

- [ ] 7.1 Write `skills/open-gui/SKILL.md`: accept a seed prompt and target cwd from the
      caller, compute the per-session state directory, start the Deno backend (which
      supervises the sidecar), write the PID/port record, and report the session URL.
- [ ] 7.2 Implement browser auto-open with a printed-URL fallback (verified unreliable
      under WSL without extra tooling — always print the URL regardless).
- [ ] 7.3 Document the fully-passive lifecycle explicitly: when invoked directly (not as
      another skill's dependency), the agent SHALL NOT proactively close the session,
      poll for completion, or end the conversation once the interaction inside the
      session appears done. Document how a user manually stops a session, using the
      recorded PID/port from the state directory.

## 8. `skills/grill-with-web/SKILL.md`: thin consumer (no server/web code)

- [ ] 8.1 Write `skills/grill-with-web/SKILL.md`: build the grilling seed prompt (topic,
      background, relevant file paths, instructions to run `grill-with-docs` unmodified,
      tree-maintenance rules using `open-gui`'s `decision`/`question` node types, and
      completion-signaling), then invoke `open-gui`'s startup procedure (Task 7.1) with
      it.
- [ ] 8.2 Implement the invoking session's completion poll against the `open-gui`
      session's `TREE.json` top-level `status`, with a timeout, plus a manual-cancel
      path that stops the backend immediately on user request.
- [ ] 8.3 On completion or cancel, stop the `open-gui` backend using its recorded PID
      (from `open-gui`'s per-session state directory — Task 3.8), and report the written
      document paths (CONTEXT.md, ADRs, `docs/grill/<slug>.md`) back to the user in the
      invoking session.
- [ ] 8.4 Instruct the seed prompt's target session to write `docs/grill/<slug>.md`
      (Mermaid diagram generated from `TREE.json` + narrative summary) at completion,
      and to set resolved `decision` nodes' `doc` field to the ADR path when one is
      produced.

## 9. Testing

- [ ] 9.1 Run the Deno tests from Task 4.2/4.3.
- [ ] 9.2 Manual smoke test — `open-gui` standalone: start the skill directly → browser
      connects (or URL fallback used) → terminal accepts input and reflects real
      `claude` output → writing nodes of all four types to `TREE.json` renders
      correctly in the tree panel → clicking a `decision`/`artifact` node with a linked
      file opens the preview → a `question` node's option cards, "Other" field, and
      notes field all correctly reach the PTY stdin → closing and reopening the browser
      tab reattaches to the live session → the session remains running after the task
      inside it appears done (no auto-close).
- [ ] 9.3 Manual smoke test — `grill-with-web` end to end: start the skill → the
      interview proceeds via `open-gui` → the tree populates with `decision` nodes →
      on completion, the `open-gui` backend shuts down (unlike the standalone case) and
      the invoking session reports correct file paths.
- [ ] 9.4 Manual test: cancel a running `grill-with-web` session from the invoking
      session and confirm the `open-gui` backend stops immediately.
