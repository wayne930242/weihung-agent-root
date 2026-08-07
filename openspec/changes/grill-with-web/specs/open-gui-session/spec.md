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
signal, and SHALL NOT proactively stop the backend process or close the session on its
own. A session runs until its caller (a user or another skill) explicitly stops it.

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
