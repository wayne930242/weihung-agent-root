## ADDED Requirements

design.md D11: this capability was originally `open-gui-terminal` (a PTY-backed
xterm.js terminal via a Node.js `node-pty` sidecar). That entire mechanism was replaced
by the Agent SDK driven directly from the Deno process — no PTY, no sidecar, no IPC
channel. Full CLI fidelity (the original goal) is achieved structurally instead: tool
calls, including `AskUserQuestion`, arrive as SDK messages rather than terminal output,
so nothing needs to be screen-scraped or keystroke-emulated to preserve it.

### Requirement: Session driven directly by the Agent SDK
The system SHALL drive the spawned `claude` session through
`@anthropic-ai/claude-agent-sdk`'s `query()`, imported directly into the Deno process via
an `npm:` specifier. No separate sidecar process and no PTY exist anywhere in this
system.

#### Scenario: One process, no sidecar
- **WHEN** an `open-gui` session starts
- **THEN** exactly one Deno process serves the frontend, the WebSocket, and the Agent SDK
  session — there is no second process to supervise or communicate with over IPC

#### Scenario: Tool calls arrive as structured messages, not terminal output
- **WHEN** the session's Claude calls any tool, including `AskUserQuestion`
- **THEN** the call arrives as a structured SDK message (`tool_use` content block, or a
  `canUseTool` callback invocation for `AskUserQuestion`) — never as raw terminal bytes to
  be parsed

### Requirement: Session message stream pushed over WebSocket
The system SHALL push the session's message stream to the connected browser as
lightly-summarized transcript entries over a WebSocket connection (`PROTOCOL.md`), and
SHALL accept free-text messages and `AskUserQuestion` answers back over the same
connection.

#### Scenario: Assistant output reaches the browser
- **WHEN** the session's Claude produces text or calls a tool
- **THEN** a corresponding transcript entry is pushed to every connected browser as a
  `transcript:event`

#### Scenario: A message reaches the session
- **WHEN** the user submits free text (the transcript pane's input box, a tree node's
  reply box, a promote-to-tree or reconsider action)
- **THEN** the corresponding text is pushed into the session's streaming input as a plain
  user message

### Requirement: Port selection avoids conflicts
The system SHALL bind its HTTP/WebSocket listener to an OS-assigned port (port 0)
rather than a fixed port number.

#### Scenario: Port is available
- **WHEN** the backend starts
- **THEN** it binds to port 0 and determines the actual assigned port before reporting
  the session URL

### Requirement: Session persists across browser disconnect
The system SHALL keep the spawned `claude` session alive on the backend regardless of
whether a browser is currently connected via WebSocket, and SHALL allow a newly
connecting browser to reattach to the same live session, replaying transcript history
and any pending question.

#### Scenario: Tab closed mid-session
- **WHEN** the user closes the browser tab while the session is still running
- **THEN** the backend keeps the Agent SDK session running and does not treat this as
  session termination

#### Scenario: Reconnecting resumes the same view
- **WHEN** the user reopens the session URL after a disconnect
- **THEN** the browser receives `transcript:snapshot` (full history), `tree:update`
  (current tree), and, if one is still outstanding, `question:ask` for the pending
  question — the same state as if it had never disconnected

### Requirement: Loud failure on session errors
The system SHALL fail with a clear, specific error message when the Agent SDK session
stream throws (e.g. the `claude` subprocess fails to spawn, an unrecoverable API error),
and SHALL NOT silently fall back to a degraded mode.

#### Scenario: Session stream throws
- **WHEN** the Agent SDK's message stream throws or the underlying `claude` process
  cannot be spawned
- **THEN** the system broadcasts a `fatal` message with the specific error before
  shutting down, rather than leaving connected browsers looking at a silently frozen
  session
