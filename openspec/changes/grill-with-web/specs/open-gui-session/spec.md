## ADDED Requirements

### Requirement: Fresh, independent session per invocation
The system SHALL start a brand-new, independent `claude` session for every `open-gui`
invocation. It SHALL NOT use `--resume` or `--continue` against the session that invoked
the skill, or any other prior session.

#### Scenario: Invocation never resumes the calling session
- **WHEN** `open-gui` is invoked from within an active terminal session
- **THEN** the system spawns a new `claude` process with a new session id, without
  passing `--resume` or `--continue`

#### Scenario: Calling session remains safe to keep using
- **WHEN** an `open-gui` session is running
- **THEN** the user may continue typing in the original terminal session concurrently
  without any risk of transcript corruption, because the two sessions never write to
  the same session file

### Requirement: Seed prompt delivered as first input
The system SHALL accept a seed prompt from its caller (a user or another skill) and
deliver it as the first input to the newly spawned `claude` process. `open-gui` SHALL
NOT impose any domain-specific structure on the seed prompt's content — that is the
caller's responsibility.

#### Scenario: Seed prompt is the new session's first input
- **WHEN** the backend spawns the new `claude` process
- **THEN** the caller-provided seed prompt is delivered as the first input to that
  process

### Requirement: Per-session state directory
The system SHALL compute a per-session state directory under
`~/.claude/state/<project-slug>/open-gui/<session-id>/` to hold that session's
`TREE.json` and process-handle record, separate from the target project's own
repository.

#### Scenario: State directory is session-scoped
- **WHEN** a new `open-gui` session starts
- **THEN** a directory unique to that session id is created under
  `~/.claude/state/<project-slug>/open-gui/`

### Requirement: Backend process handle recorded for external control
The system SHALL record the backend process's PID and assigned port in the per-session
state directory, so that a caller (a user or another skill) can locate and stop the
session, even though `open-gui` itself never reads or acts on this record.

#### Scenario: PID and port are discoverable
- **WHEN** an `open-gui` session's backend starts
- **THEN** its PID and assigned port are written to a file in that session's state
  directory before the session URL is reported

### Requirement: Browser auto-open with URL fallback
The system SHALL attempt to auto-open the user's default browser to the session URL,
and SHALL always print the full session URL regardless of whether auto-open succeeds.

#### Scenario: Auto-open fails silently
- **WHEN** the environment does not support automatic browser launching (e.g. WSL
  without additional tooling)
- **THEN** the full session URL is still printed so the user can open it manually

### Requirement: Fully passive lifecycle when used standalone
The system SHALL NOT poll `TREE.json` (or any other session state) for a completion
signal, and SHALL NOT infer that a session is "done" from task content in order to stop
the backend or close the session. A session runs until its caller (a user or another
skill) explicitly stops it, EXCEPT the two mechanical conditions below, neither of which
is a judgment call about whether the task is finished.

#### Scenario: Session left running has no auto-shutdown
- **WHEN** an `open-gui` session is invoked directly by a user (not as another skill's
  dependency) and the interview or task inside it reaches a natural end
- **THEN** the agent does not proactively close the session, stop the backend, or end
  the conversation — the session remains available until the user closes it

#### Scenario: A calling skill may still stop the session itself
- **WHEN** another skill starts an `open-gui` session as a dependency and needs to stop
  it (e.g. on its own completion or cancellation logic)
- **THEN** it does so using the recorded PID (Backend process handle requirement) — this
  is the calling skill's own behavior, not something `open-gui` performs automatically

#### Scenario: Backend shuts down when the wrapped claude process exits
- **WHEN** the spawned `claude` process exits on its own (e.g. `/exit`, a crash) rather
  than being stopped externally
- **THEN** the backend broadcasts why (so a connected browser can show it) and then
  shuts itself down shortly after — there is no session stream left for it to usefully
  serve

#### Scenario: Backend shuts down after a sustained idle period with no connections
- **WHEN** zero browser tabs have been connected to a session for 15 minutes straight
  (every tab was closed, or the browser never connected at all — e.g. auto-open silently
  failed and nobody opened the URL manually)
- **THEN** the backend shuts itself down, so a forgotten or never-opened session does not
  run unattended indefinitely

#### Scenario: A quick reconnect is unaffected by the idle timer
- **WHEN** a browser connects to a session within the 15-minute idle window (e.g. the tab
  was closed by accident and immediately reopened)
- **THEN** the idle shutdown is cancelled and the session continues running normally

#### Scenario: The browser can request an explicit stop (design.md D12)
- **WHEN** the user activates the GUI's own stop control
- **THEN** the backend shuts itself down immediately — a third explicit trigger, not an
  inferred one; the same category as the two mechanical exceptions above, since a direct
  user action is not a completion guess

### Requirement: Deterministic claude session id for manual hand-off
When spawning a real `claude` process (not a test stand-in), the system SHALL pin its
session id via `--session-id` at spawn time and record it in the per-session state
directory, so a user can later resume that same session from an ordinary terminal
without needing to parse it out of PTY output. This SHALL NOT be triggered
automatically by a browser disconnect or closed tab — only ever by explicit user
request, after the `open-gui` backend has been stopped.

#### Scenario: Session id is pinned and recorded
- **WHEN** the backend spawns a real `claude` process
- **THEN** it passes `--session-id <uuid>` and records that same id in the state
  directory's session record

#### Scenario: Closing the tab does not trigger a hand-off
- **WHEN** the user closes the browser tab
- **THEN** the backend and its `claude` session keep running exactly as they would for
  any other disconnect — no hand-off, pause, or session-id-based action happens
  automatically

#### Scenario: Manual resume from a normal terminal
- **WHEN** the user has stopped the `open-gui` session and wants to continue it from an
  ordinary terminal
- **THEN** running `claude --resume <recorded-session-id>` resumes that same session's
  transcript, picking up where the browser session left off
