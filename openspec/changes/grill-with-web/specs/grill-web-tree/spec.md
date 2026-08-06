## ADDED Requirements

### Requirement: TREE.json schema
The system SHALL define a `TREE.json` schema (in `NODE-FORMAT.md`) with a top-level
`topic` and `status` (`in_progress` | `complete`), and a `nodes` array where each node
has `id`, `parent`, `question`, `recommendation`, `status` (`open` | `resolved`), an
optional `resolution` present only when resolved, and an optional `adr` file path
present only when that decision produced an ADR.

#### Scenario: Resolved node has a resolution
- **WHEN** a node's status is `resolved`
- **THEN** the node includes a `resolution` field describing the decision

#### Scenario: Node links to its ADR when one exists
- **WHEN** a resolved decision produces an ADR under `grill-with-docs`'s sparing-ADR
  criteria
- **THEN** the corresponding node's `adr` field is set to that file's path

#### Scenario: Not every resolved node has an ADR
- **WHEN** a resolved decision does not meet the ADR criteria
- **THEN** the corresponding node has no `adr` field, and the tree still renders it as
  resolved

### Requirement: Incremental tree updates
The web-session Claude SHALL update `TREE.json` at the moment each branch resolves,
rather than batching updates to the end of the session.

#### Scenario: Node added as a question is asked
- **WHEN** the web-session Claude asks a new grilling question
- **THEN** a corresponding node is added to `TREE.json` with status `open`

#### Scenario: Node updated as it resolves
- **WHEN** the user answers an open question and it is resolved
- **THEN** that node's status is updated to `resolved` with its `resolution` in the same
  turn, not deferred

### Requirement: Live push of tree changes to the browser
The system SHALL detect changes to `TREE.json` and push them to the connected browser
over the same WebSocket connection used for terminal I/O.

#### Scenario: Tree panel updates without reload
- **WHEN** `TREE.json` changes on disk
- **THEN** the browser's tree panel reflects the change without the user reloading the
  page

### Requirement: Split-view layout with persistent tree visibility
The GUI SHALL display the terminal panel and the tree panel simultaneously in a
resizable split view, and SHALL NOT hide or collapse the tree panel by default.

#### Scenario: Both panels visible on load
- **WHEN** the browser loads the session page
- **THEN** both the terminal panel and the tree panel are visible without requiring
  additional user action

#### Scenario: Divider is resizable
- **WHEN** the user drags the divider between the two panels
- **THEN** the relative width of each panel changes accordingly

### Requirement: Node input forwards into the single PTY stream
Each tree node SHALL provide an input box whose submitted text is sent to the same PTY
stdin used by the terminal panel, and SHALL NOT create a separate conversation channel.
Submitting from a resolved node SHALL prefix the text with a reference to that node's
question.

#### Scenario: Text typed in a node reaches the terminal
- **WHEN** the user submits text from a node's input box
- **THEN** that text is sent to the PTY stdin and appears in the terminal panel's
  transcript, identically to text typed directly in the terminal

#### Scenario: Follow-up on a resolved node carries context
- **WHEN** the user submits text from a resolved node's input box
- **THEN** the text sent to the PTY is prefixed with a reference to that node's question

### Requirement: Resolved-node document preview
The system SHALL let the user open a read-only preview of a resolved node's linked
document by clicking that node, rendering the file's markdown content without leaving
the browser.

#### Scenario: Clicking a node with an ADR link opens a preview
- **WHEN** the user clicks a resolved node that has an `adr` field
- **THEN** a preview panel renders that file's markdown content

#### Scenario: Preview is read-only
- **WHEN** the document preview panel is open
- **THEN** it does not allow editing the underlying file from the GUI

#### Scenario: No preview action for nodes without a linked document
- **WHEN** the user clicks a resolved node that has no `adr` field
- **THEN** no document preview is shown for that node

### Requirement: Op-sec visual theme
The GUI SHALL use a fixed, single dark visual theme (background `#0a0c0b`, panel
`#101211`, border `#242825`, foreground `#d7ddd4`, dim text `#5c655e`, accent `#9dff5c`,
monospace typography, no glow or scanline effects), independent of the viewer's OS
light/dark preference.

#### Scenario: Theme does not follow OS preference
- **WHEN** the viewer's operating system is set to light mode
- **THEN** the GUI still renders in the fixed dark op-sec theme
