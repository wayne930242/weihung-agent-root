## ADDED Requirements

### Requirement: Generic, typed `TREE.json` schema
The system SHALL define a `TREE.json` schema (in `NODE-FORMAT.md`) with a top-level
`topic` and `status` (`in_progress` | `complete`), and a `nodes` array where every node
has a common base (`id`, `type`, `parent`, `title`) plus a `type`-specific payload. The
schema SHALL NOT be specific to any single consumer's domain (e.g. grilling); `type`
SHALL be one of `decision`, `question`, `artifact`, or `info`.

#### Scenario: Decision node payload
- **WHEN** a node's `type` is `decision`
- **THEN** it has `recommendation`, `status` (`open` | `resolved`), a `resolution` field
  required once `status` is `resolved`, and an optional `doc` file path for the preview
  panel

#### Scenario: Question node payload
- **WHEN** a node's `type` is `question`
- **THEN** it has `prompt`, an `options` array (`label`, optional `description`),
  `status` (`open` | `resolved`), and an `answer` field required once `status` is
  `resolved`

#### Scenario: Artifact node payload
- **WHEN** a node's `type` is `artifact`
- **THEN** it has a `path` field pointing to a local file to preview/embed, not a
  published URL

#### Scenario: Info node payload
- **WHEN** a node's `type` is `info`
- **THEN** it has a `text` field (markdown) and no interactive/status fields

### Requirement: Incremental tree updates
The session's Claude SHALL update `TREE.json` at the moment each node is added or
resolved, rather than batching updates to the end of the session.

#### Scenario: Node added as it is created
- **WHEN** the session's Claude introduces a new node (of any type)
- **THEN** a corresponding entry is added to `TREE.json` immediately, not deferred

#### Scenario: Node updated as it resolves
- **WHEN** an open `decision` or `question` node resolves
- **THEN** that node's `status` is updated to `resolved` with its `resolution`/`answer`
  in the same turn, not deferred

### Requirement: Live push of tree changes to the browser
The system SHALL detect changes to `TREE.json` and push them to the connected browser
over the same WebSocket connection used for terminal I/O.

#### Scenario: Tree panel updates without reload
- **WHEN** `TREE.json` changes on disk
- **THEN** the browser's tree panel reflects the change without the user reloading the
  page

### Requirement: Split-view layout with persistent tree visibility
The GUI SHALL display the terminal panel and the tree panel simultaneously in a
resizable split view by default, and SHALL NOT hide or collapse the tree panel by
default, regardless of whether any nodes have been written yet.

#### Scenario: Both panels visible on load
- **WHEN** the browser loads the session page
- **THEN** both the terminal panel and the tree panel are visible without requiring
  additional user action

#### Scenario: Divider is resizable
- **WHEN** the user drags the divider between the two panels
- **THEN** the relative width of each panel changes accordingly

#### Scenario: Empty tree renders without error
- **WHEN** `TREE.json` has no nodes yet (e.g. a session not using the tree at all)
- **THEN** the tree panel renders an empty state rather than an error

### Requirement: Per-type node rendering
The tree panel SHALL render each node differently according to its `type`, so nodes of
different kinds are visually distinguishable.

#### Scenario: Distinct visual treatment per type
- **WHEN** the tree panel renders nodes of different `type` values
- **THEN** each type's rendering reflects its distinct payload (e.g. a `decision` node
  shows its recommendation/resolution, an `info` node shows its text, an `artifact`
  node shows an embed/preview affordance, a `question` node shows its prompt and options)

### Requirement: Node interaction forwards into the single PTY stream
Each node SHALL provide an interaction affordance whose submitted text is sent to the
same PTY stdin used by the terminal panel, and SHALL NOT create a separate conversation
channel. `question`-type nodes SHALL render clickable option cards, an "Other" free-text
field, and a notes field, mirroring the `AskUserQuestion` tool's own interface; other
node types SHALL render a plain free-text box where applicable. Submitting from a
resolved node SHALL prefix the text with a reference to that node's title/prompt.

#### Scenario: Text typed in a node reaches the terminal
- **WHEN** the user submits text from a node's input box
- **THEN** that text is sent to the PTY stdin and appears in the terminal panel's
  transcript, identically to text typed directly in the terminal

#### Scenario: Selecting a question option reaches the terminal
- **WHEN** the user clicks an option card on a `question` node
- **THEN** that option's label is sent to the PTY stdin as if typed

#### Scenario: Custom reply on a question node
- **WHEN** the user types into the "Other" field on a `question` node instead of
  selecting an option
- **THEN** that free text is sent to the PTY stdin

#### Scenario: Note attached to a selection
- **WHEN** the user adds text to a `question` node's notes field alongside a selected
  option
- **THEN** the note text is included with the submission sent to the PTY stdin

#### Scenario: Follow-up on a resolved node carries context
- **WHEN** the user submits text from a resolved node's input box
- **THEN** the text sent to the PTY is prefixed with a reference to that node's
  title/prompt

### Requirement: Resolved-node document/artifact preview
The system SHALL let the user open a read-only preview of a node's linked local file
(a `decision` node's `doc`, or an `artifact` node's `path`) by clicking that node,
rendering the file's content without leaving the browser.

#### Scenario: Clicking a node with a linked file opens a preview
- **WHEN** the user clicks a `decision` node with a `doc` field, or an `artifact` node
- **THEN** a preview panel renders that file's content

#### Scenario: Preview is read-only
- **WHEN** the document/artifact preview panel is open
- **THEN** it does not allow editing the underlying file from the GUI

#### Scenario: No preview action for nodes without a linked file
- **WHEN** the user clicks a `decision` node with no `doc` field, a `question` node, or
  an `info` node
- **THEN** no preview is shown for that node

### Requirement: Op-sec visual theme
The GUI SHALL use a fixed, single dark visual theme (background `#0a0c0b`, panel
`#101211`, border `#242825`, foreground `#d7ddd4`, dim text `#5c655e`, accent `#9dff5c`,
monospace typography, no glow or scanline effects), independent of the viewer's OS
light/dark preference.

#### Scenario: Theme does not follow OS preference
- **WHEN** the viewer's operating system is set to light mode
- **THEN** the GUI still renders in the fixed dark op-sec theme
