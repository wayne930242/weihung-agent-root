## ADDED Requirements

### Requirement: Delegates session startup to `open-gui`
The system SHALL start every web-driven grill by invoking `open-gui` with a
grilling-specific seed prompt, rather than spawning its own PTY/backend/frontend. It
SHALL NOT duplicate `open-gui`'s terminal, tree-rendering, or per-session state-directory
logic.

#### Scenario: No independent backend or frontend
- **WHEN** `grill-with-web` starts a session
- **THEN** it does so by invoking `open-gui`'s startup procedure, and ships no server or
  frontend code of its own

### Requirement: Seed prompt carries grilling context and tree-maintenance rules
The system SHALL construct a seed prompt for `open-gui` containing the grilling topic,
relevant background, and relevant file paths, and SHALL instruct the new session to run
`grill-with-docs` for that topic plus rules for populating `open-gui`'s tree and
signaling completion.

#### Scenario: Seed prompt includes tree-maintenance instructions
- **WHEN** the seed prompt is constructed
- **THEN** it instructs the session to populate `open-gui`'s `TREE.json` (per
  `NODE-FORMAT.md`) using `decision`-type nodes for grilling branches — and `question`-
  type nodes when asking an `AskUserQuestion`-backed question — as each resolves, to
  write a tree-summary document at completion, and to set `TREE.json`'s top-level
  `status` to `complete` when finished

#### Scenario: Decision nodes link to their ADR
- **WHEN** a resolved decision produces an ADR under `grill-with-docs`'s sparing-ADR
  criteria
- **THEN** the corresponding `decision` node's `doc` field is set to that ADR's file path

### Requirement: Completion detection and reporting
The invoking session SHALL poll the `open-gui` session's `TREE.json` top-level `status`
field for the value `complete`, subject to a timeout, and SHALL NOT proceed to report
success without observing that value.

#### Scenario: Completion detected
- **WHEN** the web-session Claude sets `TREE.json`'s top-level `status` to `complete`
- **THEN** the invoking session's poll observes this, stops the `open-gui` backend
  (using its recorded PID — see `open-gui-session`'s Backend process handle
  requirement), and reports the written document paths back to the user in the invoking
  session

#### Scenario: Poll times out
- **WHEN** `TREE.json`'s top-level `status` does not reach `complete` within the poll
  timeout
- **THEN** the invoking session reports that the session has not completed rather than
  silently waiting indefinitely

### Requirement: Manual cancellation
The system SHALL allow the user to cancel a running `grill-with-web` session from the
invoking session at any time, without waiting for the completion signal.

#### Scenario: User cancels mid-session
- **WHEN** the user asks the invoking session to cancel a running `grill-with-web`
  session
- **THEN** the `open-gui` backend is stopped immediately (using its recorded PID),
  regardless of `TREE.json`'s current status

### Requirement: `grill-with-docs` behavior reused unmodified
The system SHALL delegate all document-writing behavior (CONTEXT.md glossary entries,
ADR criteria and format) to the existing `grill-with-docs` skill and its format files,
without duplicating or modifying that logic.

#### Scenario: Documents follow existing formats
- **WHEN** the web-session Claude resolves a branch that warrants a glossary term or ADR
- **THEN** it writes CONTEXT.md/ADR entries following the existing `CONTEXT-FORMAT.md`
  and `ADR-FORMAT.md` rules, unchanged from `grill-with-docs`
