## ADDED Requirements

### Requirement: Fresh, independent session per invocation
The system SHALL start a brand-new, independent `claude` session for every
`grill-with-web` invocation. It SHALL NOT use `--resume` or `--continue` against the
session that invoked the skill, or any other prior session.

#### Scenario: Invocation never resumes the calling session
- **WHEN** `grill-with-web` is invoked from within an active terminal session
- **THEN** the system spawns a new `claude` process with a new session id, without
  passing `--resume` or `--continue`

#### Scenario: Calling session remains safe to keep using
- **WHEN** a `grill-with-web` session is running
- **THEN** the user may continue typing in the original terminal session concurrently
  without any risk of transcript corruption, because the two sessions never write to
  the same session file

### Requirement: Seed prompt carries required context
The system SHALL construct a seed prompt for the new session containing the grilling
topic, relevant background, and relevant file paths, and SHALL instruct the new session
to run `grill-with-docs` for that topic plus the additional tree-maintenance and
completion-signaling rules.

#### Scenario: Seed prompt is the new session's first input
- **WHEN** the backend spawns the new `claude` process
- **THEN** the constructed seed prompt is delivered as the first input to that process

#### Scenario: Seed prompt includes tree-maintenance instructions
- **WHEN** the seed prompt is constructed
- **THEN** it instructs the session to update `TREE.json` per `NODE-FORMAT.md` as each
  branch resolves, to write a tree-summary document at completion, and to set
  `TREE.json`'s top-level `status` to `complete` when finished

### Requirement: Per-session state directory
The system SHALL compute a per-session state directory under
`~/.claude/state/<project-slug>/grill-web/<session-id>/` to hold that session's
`TREE.json`, separate from the target project's own repository.

#### Scenario: State directory is session-scoped
- **WHEN** a new `grill-with-web` session starts
- **THEN** a directory unique to that session id is created under
  `~/.claude/state/<project-slug>/grill-web/`

### Requirement: Completion detection and reporting
The invoking session SHALL poll the session's `TREE.json` top-level `status` field for
the value `complete`, subject to a timeout, and SHALL NOT proceed to report success
without observing that value.

#### Scenario: Completion detected
- **WHEN** the web-session Claude sets `TREE.json`'s top-level `status` to `complete`
- **THEN** the invoking session's poll observes this, stops the backend process, and
  reports the written document paths back to the user in the invoking session

#### Scenario: Poll times out
- **WHEN** `TREE.json`'s top-level `status` does not reach `complete` within the poll
  timeout
- **THEN** the invoking session reports that the session has not completed rather than
  silently waiting indefinitely

### Requirement: Manual cancellation
The system SHALL allow the user to cancel a running `grill-with-web` session from the
invoking session at any time, without waiting for the completion signal.

#### Scenario: User cancels mid-session
- **WHEN** the user asks the invoking session to cancel a running `grill-with-web` session
- **THEN** the backend process is stopped immediately, regardless of `TREE.json`'s
  current status

### Requirement: `grill-with-docs` behavior reused unmodified
The system SHALL delegate all document-writing behavior (CONTEXT.md glossary entries,
ADR criteria and format) to the existing `grill-with-docs` skill and its format files,
without duplicating or modifying that logic.

#### Scenario: Documents follow existing formats
- **WHEN** the web-session Claude resolves a branch that warrants a glossary term or ADR
- **THEN** it writes CONTEXT.md/ADR entries following the existing `CONTEXT-FORMAT.md`
  and `ADR-FORMAT.md` rules, unchanged from `grill-with-docs`
