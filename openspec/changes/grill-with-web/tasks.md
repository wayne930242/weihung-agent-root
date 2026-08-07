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

- [x] 2.1 Scaffolded `skills/open-gui/server/sidecar/` with `package.json` declaring
      `node-pty@1.1.0-beta37`. `postinstall` runs `fix-spawn-helper-permissions.js`,
      which `chmod +x`s any `spawn-helper` binaries under
      `node_modules/node-pty/{build,prebuilds}/**` (Task 1.3 finding) — confirmed firing
      on `npm install`.
- [x] 2.2 Implemented generic PTY spawning in `index.js`: the sidecar accepts a `spawn`
      IPC message (`file`, `args`, `cwd`, `env`, `cols`, `rows`) and forks exactly that —
      it decides nothing about *which* process or seed prompt to use.
- [x] 2.3 Implemented the sidecar's IPC side: a Unix domain socket (path via
      `OPEN_GUI_IPC_SOCKET`) accepting newline-delimited JSON per `PROTOCOL.md` §1.
      **Finding during verification:** the socket path must be short — macOS's
      `sockaddr_un.sun_path` limit (~104 bytes) makes `listen()`/`connect()` fail with
      `EINVAL` if nested under a long state-directory path; use a flat `/tmp/...` path
      instead (now documented in `PROTOCOL.md`).
- [x] 2.4 Loud failure implemented: `spawn` failures and malformed messages send a
      `{type:"error"}` IPC message rather than silently continuing; socket
      close/error kills the PTY child and exits the sidecar (no orphaned process).
      Verified end-to-end with a throwaway IPC client: `/bin/echo` spawn+data+exit
      round-trip, and an interactive `/bin/bash` session honoring the "wait for first
      `data` before writing" readiness rule (Task 4.1a) — both passed.

## 3. `skills/open-gui/server/`: Deno backend (serving + sidecar supervision) — done

- [x] 3.1 Scaffolded `skills/open-gui/server/` (`deno.json`, `main.ts`,
      `sidecar_client.ts`, `state.ts`, `line_framer.ts`, `schema.ts`). On startup,
      spawns and supervises the Node.js sidecar as a child process; a sidecar crash
      surfaces as a `fatal` broadcast (Task 2.4), no silent hang. Owns session-startup
      policy: sends `spawn` for the target process (`claude` by default, overridable via
      `--claude-bin` for testing), then writes the seed prompt once the sidecar's first
      `data` message arrives (readiness rule, `PROTOCOL.md` §3).
- [x] 3.2 `Deno.serve({ port: 0 }, ...)`; actual port read from `server.addr` and used to
      build the session URL.
- [x] 3.3 WebSocket endpoint (`/ws`) multiplexing `pty:write`/`pty:resize`/
      `preview:request` inbound and `pty:snapshot`/`pty:data`/`tree:update`/
      `preview:response`/`fatal` outbound, per `PROTOCOL.md` §2.
- [x] 3.4 Browser `pty:write`/`pty:resize` messages forwarded to `sidecar.write()`/
      `sidecar.resize()` over IPC.
- [x] 3.5 `Deno.watchFs` on the state dir; on a `TREE.json` create/modify event, re-reads
      the file and broadcasts `tree:update` to all connected sockets.
- [x] 3.6 `preview:request` handler reads a file relative to the target project cwd and
      responds with `preview:response` (content or error) — read-only, no write path
      exists in the protocol.
- [x] 3.7 Sidecar/PTY lifecycle is independent of WebSocket connections (the `sockets`
      Set only affects broadcast targets); a new connection replays the output ring
      buffer via `pty:snapshot` before live streaming resumes.
- [x] 3.8 Per-session state dir computed via `state.ts` (`~/.claude/state/<project-
      slug>/open-gui/<session-id>/`), seed prompt written to `seed-prompt.txt`, and
      `session.json` (`pid`, `port`, `url`) written before the "session ready" line is
      printed. **Finding:** the IPC socket must NOT live under this directory — see
      Task 2.3's finding; `state.ts`'s `ipcSocketPath()` uses a separate flat `/tmp` path.
- [x] 3.9 Proved the full chain end-to-end with `/bin/bash` standing in for `claude`
      (`--claude-bin /bin/bash`) and a throwaway Deno WS test client: seed prompt
      delivered and echoed back, `pty:snapshot` correctly replays it to a client
      connecting after the fact, `pty:write` relay confirmed round-trip, `tree:update`
      and `preview:request`/`preview:response` both confirmed. All green before any
      frontend code was written.

## 4. `TREE.json` schema and wire protocols

- [x] 4.1a Wrote `skills/open-gui/PROTOCOL.md`: the sidecar IPC envelope (newline-
      delimited JSON; PTY data stays plain UTF-8 strings inside the JSON — no base64,
      since `JSON.stringify`'s own escaping already makes embedded control bytes safe
      for line-delimited framing, as long as each write is one complete serialized
      message) and the WS message envelope (browser↔Deno: PTY I/O + snapshot-on-connect,
      tree-change push, preview request/response). Also fixes the seed-prompt readiness
      rule: wait for the sidecar's first `data` message (PTY has produced output) before
      writing the seed prompt, rather than a fixed delay.
- [x] 4.1 Wrote `skills/open-gui/NODE-FORMAT.md` defining the schema: a base node
      (`id`/`type`/`parent`/`title`) plus per-`type` payload for `decision`
      (`recommendation`/`status`/`resolution`/optional `doc`), `question`
      (`prompt`/`options[]`/`status`/`answer` with `selectedLabel`/`customText`/`notes`),
      `artifact` (local `path`), and `info` (`text`).
- [x] 4.2 `schema.ts` + `schema_test.ts`: 12 cases covering valid trees, per-type
      required fields, resolved-status field presence/absence rules for `decision` and
      `question` (including the `selectedLabel`/`customText`/"Other" answer shape),
      rejecting `status` on `artifact`/`info`, unknown `type`, and dangling `parent`
      refs. All pass (`deno test`).
- [x] 4.3 `line_framer.ts` (shared by `sidecar_client.ts`'s IPC reader) +
      `line_framer_test.ts`: 6 cases — single/multiple messages per chunk, a message
      split across chunks, embedded `\n`/`\r` inside a JSON string value not breaking
      framing (the exact concern `PROTOCOL.md` calls out), empty-line skipping, partial
      trailing data retained across feeds. All pass.

## 5. `skills/open-gui/web/`: frontend scaffold and terminal panel — done

- [x] 5.1 Scaffolded the Next.js project under `skills/open-gui/web/` with
      `output: 'export'` (static build, no Next.js runtime server, Next 16.3.0/Turbopack).
- [x] 5.2 Integrated `@xterm/xterm` + `@xterm/addon-fit`, wired to the WebSocket for PTY
      I/O (`pty:snapshot`/`pty:data`/`pty:write`/`pty:resize`, `SocketProvider.js` +
      `Terminal.js`).
- [x] 5.3 Applied the op-sec visual theme tokens, fixed regardless of OS light/dark
      preference (`app/globals.css`).

## 6. `skills/open-gui/web/`: generic tree panel — done, redesigned once per live UX feedback

- [x] 6.1 Split-view layout (`SplitView.js`) with a draggable divider; both panels
      visible by default. **Ratio revised after live user feedback** from the original
      60/40 (terminal/tree) to 35/65 — the tree, not the terminal, is the point of this
      tool. Empty-tree state confirmed rendering without error.
- [x] 6.2 Tree renders from `TREE.json`, updating live as WebSocket push events arrive —
      confirmed against a real `claude` session's own writes, not just synthetic test
      data (see Section 9's real-`claude` verification).
- [x] 6.3 Per-type node rendering, plus a small type icon (`NodeTypeIcon.js`: `◆`
      decision, `?` question, `▤` artifact, `ℹ︎` info) added after user feedback that the
      type badges alone weren't visually distinct enough.
- [x] 6.4 `question` node interaction: option cards + "Other" field + notes field, all
      funnel into `pty:write`.
- [x] 6.5 Plain free-text input for other node types; resolved-node submissions prefix
      with the node's title.
- [x] 6.6 Document/artifact preview via `PreviewPanel.js` + `preview:request`/
      `preview:response` — confirmed rendering real ADR markdown content read-only.
- [x] 6.7 (not in original plan — added from live feedback) **Master/detail redesign.**
      The original flat always-expanded list didn't read well once real tree data (7
      nodes, 2 roots, 3 levels deep) was tested — every node at full detail with an
      always-open reply box ate vertical space and gave every node equal visual weight.
      Replaced with a compact spine (`TreeSpine.js`, one row per node, VS-Code-explorer-
      style indent/connector lines, click to select) + a detail pane (`NodeDetail.js`,
      full content and interaction affordances for only the selected node). Updated
      `open-gui-tree` spec's "Node interaction..." and "Resolved-node...preview"
      requirements to describe select-then-interact instead of always-visible-inline.

## 7. `skills/open-gui/SKILL.md`: independent, passive orchestration — done

- [x] 7.1 Wrote `skills/open-gui/SKILL.md`: first-run setup (sidecar `npm install`,
      frontend build), accepts seed prompt/cwd/topic, starts the Deno backend as a
      background process, reads back the reported URL, writes/relies on the PID/port
      record (`main.ts` already writes `session.json`).
- [x] 7.2 Browser auto-open (`open <url>` on macOS) documented with an always-print-the-
      URL fallback.
- [x] 7.3 "Passive lifecycle" is a named, dedicated section: no polling, no auto-close,
      ever — that's explicitly left to a calling skill. Also documents the "For other
      skills invoking open-gui" contract (state directory as the interface: `TREE.json`
      for the calling skill's own completion detection, `session.json`'s `pid` for the
      calling skill's own shutdown) — this is what `grill-with-web` (Section 8) consumes.

## 8. `skills/grill-with-web/SKILL.md`: thin consumer (no server/web code) — done

- [x] 8.1 Wrote `skills/grill-with-web/SKILL.md`: builds the grilling seed prompt (topic,
      background, file paths, instructions to run `grill-with-docs` unmodified and
      populate `TREE.json` with `decision`/`question` nodes per `NODE-FORMAT.md`), then
      invokes `open-gui`.
- [x] 8.2 Completion poll implemented as a bounded single-shot: ~5s interval, 10-minute
      ceiling per Bash-call (design.md's Open Questions — resolved, see there for why),
      timeout reports "still running" rather than waiting silently; re-asking re-polls
      the same state directory. Manual cancel skips straight to shutdown.
- [x] 8.3 Stop-and-report step: read `session.json`'s `pid`, `SIGTERM` it (this is what
      actually closes the session, since `open-gui` never does), report the written
      document paths back to the user.
- [x] 8.4 Folded into the seed-prompt instructions (step 1) rather than a separate step —
      `docs/grill/<slug>.md` at completion, `doc` field set to the ADR path on resolved
      `decision` nodes.

## 9. Testing

- [x] 9.1 Ran the Deno tests from Task 4.2/4.3 — 18 passed, 0 failed. Re-run after the
      TCP-transport change (Section 10) and after the master/detail redesign; still
      green both times (neither touches schema/framing logic).
- [x] 9.2 Manual smoke test — `open-gui` standalone, against a **real `claude` process**
      (not just the `/bin/bash` stand-in used for earlier protocol verification): the
      real Claude Code TUI renders correctly in-browser (welcome banner, input box,
      permission/trust prompts, INSERT mode indicator) → typing and pasting both reach
      the process and get real responses → all four node types render distinctly in the
      tree, generated by a real `claude` session (not a hand-written fixture) → doc
      preview renders real ADR markdown read-only → `question` node option cards +
      "Other" field + notes field all confirmed reaching the PTY stdin →
      `pty:snapshot`-based reconnect confirmed for the scrollback-replay case (bash-
      based). **Not yet exercised**: reconnect against a real `claude` session's
      alternate-screen buffer specifically (flagged as an open risk in design.md) —
      everything else in this scenario is now confirmed working, this one path isn't.
- [ ] 9.3 Manual smoke test — `grill-with-web` end to end: **in progress (2026-08-07).**
      A real session (real `claude` binary, topic "Greeting casing convention" against a
      throwaway scratch project) is live — seed delivery confirmed working (see 10.15)
      and the interview has started. Still open: reaching `TREE.json` `status: complete`,
      `docs/grill/<slug>.md` actually being written, and the completion-poll →
      `SIGTERM` → report chain (step 3/4 of `grill-with-web/SKILL.md`) — none of that is
      confirmed yet, don't mark this done until it is.
- [ ] 9.4 Manual test: cancel a running `grill-with-web` session from the invoking
      session and confirm the `open-gui` backend stops immediately. Not run (depends on
      9.3 existing first).

## 10. Post-implementation hardening (not in the original plan — found during Section 9)

Real-`claude` testing (Task 9.2) surfaced three genuine bugs no `/bin/bash`-based test
had exercised, plus two portability gaps raised directly by the user after seeing the
live UI. All fixed and re-verified; recorded here since they're real scope this change
delivered, not just the originally-planned 40 tasks.

- [x] 10.1 Fixed: fast keystrokes silently dropped (`sidecar_client.ts` writer-lock
      contention — see design.md, after D9). Verified via rapid real typing post-fix.
- [x] 10.2 Fixed: `TREE.json` writes via atomic write-then-rename never triggered a live
      push (`Deno.watchFs` event-kind filter excluded `rename`). Verified live against a
      real `claude` `Write` tool call.
- [x] 10.3 Fixed: spawned `claude` process inherited this harness's own
      `CLAUDE_CODE_CHILD_SESSION` env marker, contradicting D1. Fixed via
      `independentSpawnEnv()` filtering all `CLAUDE`-prefixed vars from the spawn env.
- [x] 10.4 Fixed: seed prompt with an embedded/trailing newline landed in the chat input
      but never submitted (raw PTY treats embedded `\n` as "insert line", not "submit").
      Fixed by collapsing to one logical line before the terminal `\r`.
- [x] 10.5 **Windows portability** (user-raised): confirmed via Deno's own docs that
      `transport: "unix"` has no Windows support at all — a hard blocker, not a
      theoretical gap. Switched sidecar IPC from a Unix domain socket to a TCP loopback
      socket (`127.0.0.1`, OS-assigned port); this also incidentally removes the
      macOS `sockaddr_un.sun_path` length limit found earlier. Re-verified the full
      chain end-to-end post-switch. Added `HOME`/`USERPROFILE` fallback and
      backslash-aware path splitting in `state.ts` for Windows. **Still unverified**:
      no Windows machine available this session — `Deno.watchFs` event-kind behavior on
      Windows and the sidecar's install step are unexercised there (see design.md's
      Open Questions).
- [x] 10.6 **Init script** (user-requested): `skills/open-gui/init.sh` (macOS/Linux,
      tested idempotent on this machine) and `init.ps1` (Windows, untested) — install
      Deno if missing, check Node.js, install sidecar + frontend deps, build the
      frontend. `open-gui/SKILL.md`'s first-run-setup step now just runs this instead of
      inlining the same logic as prose.
- [x] 10.7 **Deterministic session id + manual terminal hand-off** (user-requested,
      design.md D10): real `claude` spawns now pin `--session-id <uuid>` (verified via
      `claude --help` that this flag exists and accepts a UUID), recorded as
      `claudeSessionId` in `session.json` and printed at startup. Verified end-to-end:
      had a real conversation via the browser, stopped the `open-gui` backend, ran
      `claude --resume <id>` in a plain terminal, confirmed it recalled the conversation
      correctly. Deliberately NOT triggered automatically by tab-close/disconnect — see
      `open-gui-session` spec's "Deterministic claude session id for manual hand-off"
      requirement and `SKILL.md`'s "Switch to a normal terminal" section for why.
- [x] 10.8 Browser auto-open strengthened to explicitly require foreground/focus
      (user-raised — the point of auto-open is defeated if the window doesn't surface),
      and made genuinely cross-platform in `SKILL.md` (`open`/`xdg-open`/`start`) rather
      than only documenting the macOS command.
- [x] 10.9 Fixed: terminal panel rendered garbled/wrong-sized on first load, only
      self-correcting after a manual divider drag (user-raised, with a screenshot).
      Root cause: `Terminal.js` registered `t.onResize()` *after* the mount-time
      `fitAddon.fit()` call, so that first resize event — the one that would have told
      the backend the PTY's real size — fired with no listener attached and was lost;
      every later `fit()` computed the same already-applied size and produced no new
      event, until a genuinely different size (a user drag) finally did. Fixed by
      registering `onResize` before the first `fit()`. Verified via `claude-in-chrome`:
      a fresh session's PTY reported a non-default size (`tput cols`/`tput lines`) with
      no manual resize.
- [x] 10.10 **Theme follows Claude Code's own config** (user-raised, design.md D7
      revision): backend reads `~/.claude/settings.json`'s `theme` (best-effort,
      defaults dark), sends it as a `config` WS message; frontend applies it via a
      `data-theme` attribute (`globals.css` light palette) and mirrors it into the
      embedded terminal's own xterm theme so both panels match. Verified visually via
      `claude-in-chrome` against both a real dark-default session and a session with a
      fake `HOME` pointing at a `"theme": "light"` settings file, including with real
      tree content (not just an empty tree) to check contrast/readability.
- [x] 10.11 **Artifact `url` kind** (user-raised, design.md D9 revision): `artifact`
      nodes gained a `kind` field (`file` default | `url`); `url`-kind nodes iframe a
      claude.ai artifact link directly plus an "open in new tab" button, accepting that
      a non-shared link shows claude.ai's own sign-in wall inside the iframe rather than
      content. `schema.ts`/`schema_test.ts`/`NODE-FORMAT.md`/`open-gui-tree` spec
      updated; verified visually via `claude-in-chrome` with a real public URL.
- [x] 10.12 **Optimistic pending indicator + node-id-tagged submissions**
      (user-raised): a node the user just answered shows a local-only "pending" state
      in the spine and detail pane until the next `tree:update` shows that specific
      node's own data changed (never written to `TREE.json` — see open-gui-tree spec's
      new "Optimistic pending indicator" requirement). `lib/submission.js`'s
      `buildSubmission` tags every submission with the originating node's id/title, not
      only resolved-node ones (this was the concrete bug behind the "claude didn't know
      which question I was answering" report) — see the updated "Every submission
      carries node context" scenario. Verified via `claude-in-chrome`: submitted text
      showed `Re "..." [q1]: ...` in the terminal; the pending badge appeared
      immediately, survived an unrelated node's `TREE.json` change, and cleared once
      that specific node's own data changed.
- [x] 10.13 **Tree spine keyboard navigation + question quick-answer** (user-raised):
      vim (`j`/`k`) and native arrow keys move the spine selection (inert while a text
      input has focus); a selected `question` node accepts digit keys `1`-`4` to submit
      the matching option, `n` to focus the notes field, and the "Other" field submits
      on Enter with an IME-composition guard. See open-gui-tree spec's new "Tree spine
      keyboard navigation" and "Question node keyboard quick-answer" requirements.
      Verified via `claude-in-chrome`: arrow-key navigation moved the selection through
      the depth-first spine order, digit key `2` submitted the second option card, and
      `n` moved focus to the notes textarea.
- [x] 10.19 **Seed prompts must embed content, not reference it** (user-raised: "他還跑
      去讀取 skill 又跑去看 gui...浪費很多時間" after watching a fresh grill-with-web
      session spend its first turn invoking the `Skill` tool for `grill-with-docs` and
      hunting for `NODE-FORMAT.md` — a failed background search plus 30s+ before it even
      started the actual interview). Root cause: the seed prompt told the target session
      to "run grill-with-docs" / "populate TREE.json per NODE-FORMAT.md" — bare
      references a fresh session with nothing loaded has to resolve itself, instead of
      the calling skill (which already has `Read` access) just reading those files and
      writing their actual content into the seed prompt. Fixed in both
      `open-gui/SKILL.md` ("For other skills invoking open-gui") and
      `grill-with-web/SKILL.md` step 1 — rewritten to say explicitly: read
      `grill-with-docs`/`NODE-FORMAT.md` yourself, embed their instructions/node shapes
      directly, never just point at them by name or path.
- [x] 10.18 **Two mechanical exceptions to "never shuts itself down"** (user-raised
      twice: wanted the backend to stop when the `claude` session inside it closes, and
      separately flagged that closing a tab doesn't stop the server — worried about
      processes accumulating over repeated use). `main.ts`: (a) shuts down ~500ms after
      the wrapped `claude` process exits on its own, broadcasting `session:ended` first
      (`SessionEndedBanner.js`, distinct neutral wording from `FatalBanner` — not
      necessarily an error); (b) shuts down after 15 minutes with zero open WebSocket
      connections (covers both "every tab closed" and "browser auto-open silently
      failed, nobody ever connected"), cancelled by any connection within that window.
      Verified (a) live: typed `exit` in a `/bin/bash` stand-in session, banner appeared
      within ~1s, `ps` confirmed the Deno process actually exited ~1s later. Verified (b)
      live too, with `IDLE_SHUTDOWN_MS` temporarily lowered (10s) rather than waiting the
      real 15 minutes: confirmed a session that's never connected shuts down on schedule,
      and separately that a reconnect within the window cancels the pending shutdown and
      a fresh idle window starts once that connection later closes for real — reverted to
      15 minutes after. See design.md's D8 revision and open-gui-session spec's rewritten
      "Fully passive lifecycle" requirement.
- [x] 10.17 **`AskUserQuestion` is a raw-mode menu, not a text prompt — real
      submission protocol found and implemented** (user-raised after live testing:
      "問題沒有變成 tree", option-card clicks did nothing). Confirmed live against
      `grillweb4`: sending an option's label text does nothing (paste-detection
      swallows it, same root cause as 10.15); a bare digit keystroke (no `\r`) for a
      real option selects+confirms in one step; the widget's trailing "N+1 Type
      something"/"N+2 Chat about this" entries need a digit + a *separate* `\r`, and
      confirming "Type something" cancels the tool call back to the normal chat prompt
      rather than opening an in-widget text field. `QuestionNode.js` rewritten: option
      cards send `String(index)`; "Other" sends `options.length + 1`, waits, sends
      `\r`, waits, sends the free text; notes now go out as a separate follow-up
      message (can no longer ride along with an option pick). See design.md D5's
      revision and open-gui-tree spec's rewritten "Node interaction forwards..."
      requirement. **Known open gap, not fixed here:** assumes the node's menu is
      still the live thing on screen at submission time.
- [x] 10.16 **Manual theme override** (user-raised, in case backend detection of
      Claude Code's `theme` setting doesn't land in some environment): a small
      `auto`/`dark`/`light` toggle in the tree header (`ThemeToggle.js`), persisted in
      `localStorage` (`SocketProvider.js`'s `themeOverride`) — `auto` defers to the
      backend-detected theme, `dark`/`light` win over it. Verified via `claude-in-chrome`:
      cycling the control switched both panels to the light palette regardless of the
      backend's dark config, and survived a page reload.
- [x] 10.15 Fixed: **actually running Task 9.3 for the first time** (real `claude`
      binary, real `grill-with-docs` interview) surfaced a real seed-prompt-delivery
      bug: the seed landed in the input box collapsed into a `[Pasted text #1 +1
      lines]` chip and never submitted, because Claude Code's TUI detects a long
      single-write burst as a paste and the trailing `\r` sent in that same write gets
      absorbed into the paste event instead of registering as a separate submit
      keystroke. Fixed by splitting `scheduleSeedSend` (`main.ts`) into two writes —
      the seed text, then `\r` 200ms later. Verified live via `claude-in-chrome`: the
      seed prompt now submits and the target session starts working immediately. See
      design.md's "Seed-prompt delivery timing" Open Question — the narrower
      unpredictable-first-run-gate risk documented there separately remains open.
- [x] 10.14 Fixed: found while finally preparing to run Task 9.3 — no calling skill's
      seed prompt had a way to tell the target session where to write `TREE.json` (the
      spawned `claude` process's own `--session-id` is a different id from the one that
      determines the state directory, and it's never passed as an env var). Would have
      silently produced a live tree that never populates. Fixed in `open-gui/SKILL.md`
      ("For other skills invoking open-gui") and `grill-with-web/SKILL.md` step 1: the
      calling skill must compute and embed the literal `TREE.json` path in the seed
      prompt, not just reference the schema doc.
