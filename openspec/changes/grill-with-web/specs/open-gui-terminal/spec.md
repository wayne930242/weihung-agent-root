## ADDED Requirements

### Requirement: Full-fidelity interactive terminal
The system SHALL render the spawned `claude` process's real interactive CLI in the
browser via a PTY-backed terminal, including permission prompts, tool use output, and
slash commands, indistinguishable in behavior from running `claude` directly in a
terminal.

#### Scenario: Permission prompt appears in-browser
- **WHEN** the spawned `claude` process requires a tool-use permission confirmation
- **THEN** the prompt renders in the browser terminal exactly as it would in a native
  terminal, and the user's response is sent back to the same process

#### Scenario: No degraded/headless behavior
- **WHEN** the browser terminal is active
- **THEN** it reflects the process's real PTY output (ANSI, spinners, redraws) rather
  than a parsed or simplified representation

### Requirement: Deno process handles serving, a Node.js sidecar owns the PTY
The system SHALL use one Deno process to serve the frontend and WebSocket connection,
and SHALL delegate PTY spawning and I/O exclusively to a Node.js sidecar process
dedicated to `node-pty`, communicating over a local IPC channel. No separate frontend
server process exists, and the Deno process SHALL NOT attempt to load `node-pty` itself.

#### Scenario: One Deno process handles serving
- **WHEN** an `open-gui` session starts
- **THEN** exactly one Deno process is responsible for the static frontend and the
  WebSocket, relaying PTY I/O to/from the Node.js sidecar over IPC

#### Scenario: Sidecar owns the PTY exclusively
- **WHEN** the backend spawns the target `claude` process
- **THEN** the Node.js sidecar process performs the PTY fork and all reads/writes to it,
  not the Deno process

### Requirement: PTY I/O streamed over WebSocket
The system SHALL stream the PTY's stdin/stdout as bytes over a WebSocket connection to
the browser, and SHALL forward browser keystrokes back to the PTY's stdin over the same
connection.

#### Scenario: Output reaches the browser
- **WHEN** the spawned `claude` process writes to its PTY
- **THEN** that output is relayed by the sidecar to the Deno process over IPC and pushed
  to the connected browser over the WebSocket

#### Scenario: Keystrokes reach the process
- **WHEN** the user types in the browser terminal
- **THEN** the corresponding bytes are forwarded by the Deno process to the sidecar over
  IPC and written to the PTY's stdin

### Requirement: Port selection avoids conflicts
The system SHALL bind its HTTP/WebSocket listener to an OS-assigned port (port 0)
rather than a fixed port number.

#### Scenario: Port is available
- **WHEN** the backend starts
- **THEN** it binds to port 0 and determines the actual assigned port before reporting
  the session URL

### Requirement: Session persists across browser disconnect
The system SHALL keep the spawned `claude` process and PTY alive on the backend
regardless of whether a browser is currently connected via WebSocket, and SHALL allow a
newly connecting browser to reattach to the same live session.

#### Scenario: Tab closed mid-session
- **WHEN** the user closes the browser tab while the session is still running
- **THEN** the backend keeps the sidecar and PTY process running and does not treat this
  as session termination

#### Scenario: Reconnecting resumes the same view
- **WHEN** the user reopens the session URL after a disconnect
- **THEN** the browser reconnects to the same live PTY session and its current state

### Requirement: Loud failure on PTY dependency errors
The system SHALL fail with a clear, specific error message when the Node.js sidecar or
`node-pty` cannot start (e.g. missing native build tools, sidecar process crash, IPC
channel failure to establish), and SHALL NOT silently fall back to a degraded mode.

#### Scenario: node-pty fails to build or the sidecar fails to start
- **WHEN** `node-pty` cannot be built/loaded, or the sidecar process fails to start or
  connect over IPC
- **THEN** the system reports the specific failure and what is needed to resolve it,
  rather than starting in a degraded or non-functional state
