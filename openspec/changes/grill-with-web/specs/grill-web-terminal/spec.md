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

### Requirement: Single backend process for PTY and serving
The system SHALL use one Deno process to both spawn the PTY-wrapped `claude` process and
serve the frontend and WebSocket connection — no separate frontend server process.

#### Scenario: One process handles both roles
- **WHEN** a `grill-with-web` session starts
- **THEN** exactly one Deno process is responsible for the PTY subprocess, the static
  frontend, and the WebSocket

### Requirement: PTY I/O streamed over WebSocket
The system SHALL stream the PTY's stdin/stdout as bytes over a WebSocket connection to
the browser, and SHALL forward browser keystrokes back to the PTY's stdin over the same
connection.

#### Scenario: Output reaches the browser
- **WHEN** the spawned `claude` process writes to its PTY
- **THEN** that output is pushed to the connected browser over the WebSocket

#### Scenario: Keystrokes reach the process
- **WHEN** the user types in the browser terminal
- **THEN** the corresponding bytes are written to the PTY's stdin

### Requirement: Port selection avoids conflicts
The system SHALL bind its HTTP/WebSocket listener to an OS-assigned port (port 0)
rather than a fixed port number.

#### Scenario: Port is available
- **WHEN** the backend starts
- **THEN** it binds to port 0 and determines the actual assigned port before reporting
  the session URL

### Requirement: Browser auto-open with URL fallback
The system SHALL attempt to auto-open the user's default browser to the session URL,
and SHALL always print the full session URL regardless of whether auto-open succeeds.

#### Scenario: Auto-open fails silently
- **WHEN** the environment does not support automatic browser launching (e.g. WSL
  without additional tooling)
- **THEN** the full session URL is still printed so the user can open it manually

### Requirement: Session persists across browser disconnect
The system SHALL keep the spawned `claude` process and PTY alive on the backend
regardless of whether a browser is currently connected via WebSocket, and SHALL allow a
newly connecting browser to reattach to the same live session.

#### Scenario: Tab closed mid-session
- **WHEN** the user closes the browser tab while the session is still running
- **THEN** the backend keeps the PTY process running and does not treat this as
  session termination

#### Scenario: Reconnecting resumes the same view
- **WHEN** the user reopens the session URL after a disconnect
- **THEN** the browser reconnects to the same live PTY session and its current state

### Requirement: Loud failure on PTY dependency errors
The system SHALL fail with a clear, specific error message when `node-pty` cannot be
loaded or built (e.g. missing native build tools), and SHALL NOT silently fall back to a
degraded mode.

#### Scenario: node-pty fails to build
- **WHEN** `node-pty` cannot be built or loaded in the current environment
- **THEN** the system reports the specific failure and what is needed to resolve it,
  rather than starting in a degraded or non-functional state
