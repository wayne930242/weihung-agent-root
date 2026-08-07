# open-gui wire protocols

Two protocols, fixed here before either side is implemented (Task 4.1a). Both are
newline-delimited JSON: one JSON object serialized with `JSON.stringify`, one `\n`.
There is no raw-byte framing anywhere in this system — every message is a JSON object.

This is safe for PTY output despite ANSI/control bytes because a writer never appends a
raw byte stream to a line; it always serializes the *whole message* first. Standard JSON
string escaping turns embedded `\n`, `\r`, and control bytes into `\\n`, `\\r`, `\uXXXX`
inside the string value, so the record separator (the one real `\n` after the JSON
object) never collides with payload content. The one discipline this requires: a writer
must flush exactly one complete serialized line per message — never a partial write,
never two messages concatenated without a separator.

PTY bytes are never base64-encoded. `node-pty` is spawned with `encoding: "utf8"`, and
Node's stream decoder (`StringDecoder`) buffers incomplete multi-byte UTF-8 sequences
until a full character is available before emitting a chunk — so `onData` already hands
us complete, valid UTF-8 strings, safe to drop straight into a JSON string field.

## 1. Sidecar IPC (Deno process ↔ Node.js sidecar)

Transport: a **TCP loopback socket** (`127.0.0.1`, OS-assigned port) — not a Unix domain
socket. Two independent reasons ruled that out: Deno's `transport: "unix"` [has no
Windows support at all](https://docs.deno.com/api/deno/~/Deno.UnixConnectOptions.transport)
(confirmed against Deno's own docs — this is a hard platform gap, not a rough edge), and
separately, macOS's `sockaddr_un.sun_path` limit (~104 bytes) made `listen()`/`connect()`
fail with `EINVAL` once the socket path was nested under a sufficiently long state
directory (confirmed via smoke test before the transport was changed). A loopback TCP
socket has neither problem and needs no special-casing per OS.

The sidecar binds port 0 on `127.0.0.1` and prints `READY <port>\n` to its own stdout
once listening. Deno reads that line (not a fixed delay) to learn which port to connect
to as the client, retrying briefly until the sidecar is ready.

One sidecar process handles exactly one PTY (one `open-gui` session = one Deno process =
one sidecar = one PTY). No session/connection id field is needed in either direction.
Binding to loopback only (never `0.0.0.0`) keeps this IPC channel unreachable from
outside the machine — it carries unauthenticated `spawn`/`write` control messages, so
that's a real boundary, not a formality.

**Deno → sidecar:**

| `type`   | fields                                                  | meaning                          |
|----------|----------------------------------------------------------|-----------------------------------|
| `spawn`  | `file`, `args[]`, `cwd`, `env`, `cols`, `rows`            | fork exactly this — the sidecar decides nothing about *which* process to run; that policy lives in the Deno backend (see §3, Task 3.1) |
| `write`  | `data` (string)                                           | write to the PTY's stdin          |
| `resize` | `cols`, `rows`                                            | resize the PTY                    |

**Sidecar → Deno:**

| `type`     | fields                          | meaning                                   |
|------------|----------------------------------|--------------------------------------------|
| `spawned`  | `pid`                            | ack for `spawn`, carries the child's PID   |
| `data`     | `data` (string)                  | a chunk of PTY output                      |
| `exit`     | `code`, `signal`                 | the spawned process exited                 |
| `error`    | `message`                        | spawn failed or a runtime PTY error occurred — the sidecar does not attempt recovery, this is a terminal condition for the session (see `open-gui-terminal`'s loud-failure requirement) |

**Process lifecycle:** the Deno process registers a `SIGTERM`/`SIGINT` handler that
explicitly kills the sidecar (which kills its PTY child in turn) before exiting — child
processes are not reaped automatically on parent death. As defense against an ungraceful
Deno crash, the sidecar also treats its IPC socket closing/erroring as a signal to kill
its PTY child and exit itself, rather than lingering.

## 2. Browser WebSocket (browser ↔ Deno)

One WebSocket connection per browser tab, JSON text frames. Multiplexes PTY I/O, tree
push, and doc/artifact preview.

**Browser → Deno:**

| `type`             | fields                        | meaning                                                                 |
|--------------------|--------------------------------|---------------------------------------------------------------------------|
| `pty:write`         | `data` (string)                | keystrokes/text to send to the PTY stdin — this is the single funnel every node interaction (terminal typing, node free-text box, question option click, "Other" reply, notes) ultimately writes to, per design.md D5 |
| `pty:resize`        | `cols`, `rows`                 | terminal panel was resized                                              |
| `preview:request`   | `requestId`, `path`            | request a local file's contents for the read-only preview panel          |

**Deno → browser:**

| `type`             | fields                                  | meaning                                                                 |
|--------------------|-------------------------------------------|---------------------------------------------------------------------------|
| `config`            | `theme` (`"dark"` \| `"light"`)           | sent once, immediately on connect: the host's Claude Code theme preference (best-effort read of `~/.claude/settings.json`, default `"dark"` — design.md D7 revision) |
| `pty:snapshot`      | `data` (string)                           | sent once, immediately on connect: the full buffered output since the PTY was spawned (bounded ring buffer — see below), so a (re)connecting browser sees current terminal state before live streaming resumes |
| `pty:data`          | `data` (string)                           | a live chunk of PTY output (post-snapshot)                               |
| `tree:update`       | `tree` (full `TREE.json` contents)        | sent once immediately on connect with current state, then again on every `TREE.json` change — always the full document, never a diff (the file is small; diffing isn't worth the complexity) |
| `preview:response`  | `requestId`, `content` or `error`         | response to a `preview:request`                                          |
| `fatal`             | `message`                                 | an unrecoverable backend error (e.g. sidecar `error`) — the browser SHOULD render this prominently; the backend does not attempt to continue serving PTY I/O afterward |
| `session:ended`     | `code`, `signal`                          | the wrapped `claude` process exited (cleanly or not) — the backend broadcasts this and then shuts itself down (~500ms later); the browser SHOULD render this distinctly from `fatal` (not an error — the session may have ended intentionally, e.g. the user ran `/exit`) |

**Output buffering for reconnect:** the Deno process keeps an in-memory ring buffer of
all PTY output emitted since spawn (bounded — last ~1MB), independent of any WebSocket
connection state. This is what `pty:snapshot` replays on (re)connect. This is a
scrollback replay, not full terminal-state serialization (cursor position, alternate
screen buffer) — acceptable for this tool's scope; xterm.js re-renders the replayed
bytes through its own parser same as if they'd streamed live.

**Idle shutdown:** independent of `session:ended`, the backend also shuts itself down
(no broadcast — by definition nobody is connected) after 15 minutes with zero open
WebSocket connections, whether that's because every tab was closed or because the
browser never connected in the first place (e.g. auto-open silently failed). Any new
connection within that window cancels the timer.

## 3. Seed-prompt delivery timing

`claude` is an interactive TUI; it is not ready to receive input the instant the process
forks. Task 1.3's smoke test needed a fixed delay before `p.write()` had any visible
effect — writing immediately after `spawn` races the TUI mounting and the seed prompt is
silently lost (typed into nothing).

**Rule:** the Deno backend waits for the first `data` message from the sidecar (i.e. the
PTY has produced its first output — the TUI has started drawing) before sending the seed
prompt via `write`. This is an output-match readiness signal, not a fixed delay — more
robust across machines than guessing a timeout, and simple to implement (it's just "hold
the seed-prompt write until after the first `data` event, then send it, then resume
normal relay").

