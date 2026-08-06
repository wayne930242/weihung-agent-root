## 1. Environment verification (de-risk first)

- [ ] 1.1 In the target environment, verify `npm:node-pty@1.1.0-beta37`+ actually spawns
      and reads/writes a PTY correctly under Deno (see design.md D3/Open Questions).
- [ ] 1.2 If it fails or is unstable, fall back to the documented Node.js sidecar
      approach (small dedicated `node-pty` process, IPC to the Deno backend) before
      proceeding to Section 2.

## 2. Backend: Deno server skeleton

- [ ] 2.1 Scaffold `skills/grill-with-web/server/` with `deno.json` declaring the
      `npm:node-pty` dependency.
- [ ] 2.2 Implement PTY spawn of a fresh, independent `claude` process (new session id,
      cwd = target project, no `--resume`/`--continue`), fed the seed prompt as first input.
- [ ] 2.3 Bind `Deno.serve()` to port 0 (OS-assigned) and read back the actual port.
- [ ] 2.4 Fail loudly with a specific, actionable error if `node-pty` fails to build or
      load — no silent degraded mode.

## 3. Backend: WebSocket protocol

- [ ] 3.1 Implement the WebSocket endpoint multiplexing three message types: PTY I/O
      bytes, `TREE.json` change events, and doc-preview file-content requests.
- [ ] 3.2 Forward browser-submitted keystrokes/text (including tree node input) to the
      PTY's stdin.
- [ ] 3.3 Watch the session's `TREE.json` for changes and push updates over the WebSocket.
- [ ] 3.4 Implement the doc-preview request handler: read a given file path under the
      target project and return its contents (read-only, no write path).
- [ ] 3.5 Ensure the PTY process and WebSocket serving survive browser disconnects —
      reconnecting to the same session URL reattaches to the live PTY.

## 4. TREE.json schema

- [ ] 4.1 Write `skills/grill-with-web/NODE-FORMAT.md` defining the schema: top-level
      `topic`/`status`, `nodes[]` with `id`/`parent`/`question`/`recommendation`/
      `status`/`resolution`/optional `adr`.
- [ ] 4.2 Write a Deno test validating `TREE.json` against this schema (structure and
      required-field-per-status rules).
- [ ] 4.3 Write a Deno test for the WebSocket message framing/parsing (Task 3.1).

## 5. Frontend: scaffold and terminal panel

- [ ] 5.1 Scaffold the Next.js project under `skills/grill-with-web/web/` with
      `output: 'export'` (static build, no Next.js runtime server).
- [ ] 5.2 Integrate xterm.js, wired to the WebSocket for PTY I/O.
- [ ] 5.3 Apply the op-sec visual theme tokens (background `#0a0c0b`, panel `#101211`,
      border `#242825`, foreground `#d7ddd4`, dim `#5c655e`, accent `#9dff5c`,
      monospace, no glow/scanlines), fixed regardless of OS light/dark preference.

## 6. Frontend: tree panel

- [ ] 6.1 Build the split-view layout: terminal (left, ~60%) and tree panel (right,
      ~40%) with a draggable divider; both panels visible by default.
- [ ] 6.2 Render the tree from `TREE.json`, updating live as WebSocket push events arrive.
- [ ] 6.3 Add per-node input boxes that send submitted text to the PTY stdin over the
      WebSocket; resolved-node submissions prefix the text with a reference to that
      node's question.
- [ ] 6.4 Add the resolved-node document preview: clicking a node with an `adr` field
      requests and renders that file's markdown in a read-only slide-over panel.

## 7. Orchestration: SKILL.md

- [ ] 7.1 Write `skills/grill-with-web/SKILL.md`: compute the per-session state
      directory (`~/.claude/state/<project-slug>/grill-web/<session-id>/`), build the
      seed prompt (topic, background, relevant file paths, plus the tree-maintenance
      and completion-signaling instructions), and start the backend.
- [ ] 7.2 Implement browser auto-open with a printed-URL fallback (verified unreliable
      under WSL without extra tooling — always print the URL regardless).
- [ ] 7.3 Implement the invoking session's completion poll against `TREE.json`'s
      top-level `status`, with a timeout, plus a manual-cancel path that stops the
      backend immediately on user request.
- [ ] 7.4 On completion, stop the backend process and report the written document paths
      (CONTEXT.md, ADRs, `docs/grill/<slug>.md`) back to the user in the invoking session.
- [ ] 7.5 Instruct the seed prompt's target session to run `grill-with-docs` unmodified
      for the interview itself, plus write `docs/grill/<slug>.md` (Mermaid diagram
      generated from `TREE.json` + narrative summary) at completion.

## 8. Testing

- [ ] 8.1 Run the Deno tests from Task 4.2/4.3.
- [ ] 8.2 Manual smoke test: start the skill → browser connects (or URL fallback used)
      → terminal accepts input and reflects real `claude` output → tree panel updates
      live as nodes resolve → clicking a resolved node with an ADR link opens the doc
      preview → typing in a node's input box shows up in the terminal → closing and
      reopening the browser tab reattaches to the live session → on completion, the
      backend shuts down and the invoking session reports correct file paths.
- [ ] 8.3 Manual test: cancel a running session from the invoking session and confirm
      the backend stops immediately.
