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
- **THEN** it has a `kind` field (`file` | `url`, default `file`); `file`-kind nodes have
  a `path` pointing to a local file to preview, `url`-kind nodes have a `url` pointing to
  a published `claude.ai` artifact to embed

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
The tree panel SHALL render as a master/detail pair: a compact spine listing every node
as one row, and a detail pane showing the full content of whichever node is currently
selected. Interaction affordances (reply boxes, option cards, the "Other" field, the
notes field) SHALL render only in the detail pane for the selected node, not inline for
every node at once. Each node SHALL provide an interaction affordance whose submitted
text is sent to the same PTY stdin used by the terminal panel, and SHALL NOT create a
separate conversation channel. `question`-type nodes SHALL render clickable option
cards, an "Other" free-text field, and a notes field, mirroring the `AskUserQuestion`
tool's own interface; other node types SHALL render a plain free-text box where
applicable. Every submission, regardless of the originating node's `status`, SHALL be
prefixed with a reference to that node's id and title, so the receiving `claude` process
can identify which node is being answered even when multiple nodes are open at once —
except a question node's option-card selection itself, which is a bare positional
keystroke, not text (see below).

Empirically verified (2026-08-07) against a real `claude` session: `AskUserQuestion`
renders as a raw-mode menu widget, not a text prompt. Typing an option's label as PTY
input does nothing useful for it (a long single-write burst instead trips the same
paste-detection that swallowed the seed prompt, `main.ts`'s `SEED_SUBMIT_DELAY_MS` fix).
The system SHALL instead send a bare digit keystroke matching the option's 1-based
position — this selects AND confirms it in one step, with no trailing `\r`. This is a
known, accepted staleness risk: it assumes the terminal is still showing *this* node's
menu at the moment of submission; a stale node's keystroke lands on whatever the
terminal actually shows right now.

#### Scenario: Text typed in a node reaches the terminal
- **WHEN** the user selects a node in the spine and submits text from its detail pane's
  input box
- **THEN** that text is sent to the PTY stdin and appears in the terminal panel's
  transcript, identically to text typed directly in the terminal

#### Scenario: Selecting a question option reaches the terminal
- **WHEN** the user selects a `question` node in the spine and clicks an option card in
  its detail pane
- **THEN** a single digit keystroke matching that option's 1-based position among the
  node's `options` is sent to the PTY stdin, with no trailing Enter and no label text

#### Scenario: Custom reply on a question node
- **WHEN** the user types into the "Other" field in a `question` node's detail pane
  instead of selecting an option
- **THEN** the system sends the digit keystroke one past the node's last real option
  (`options.length + 1`, matching the widget's own "Type something" menu entry),
  followed by a separate `\r` to confirm it — which exits the menu back to the normal
  chat prompt — followed by the free text (as an ordinary chat message, prefixed per the
  node-context rule below)

#### Scenario: Note attached to a selection
- **WHEN** the user adds text to a `question` node's notes field in its detail pane
  alongside a selected option
- **THEN** the note text is sent as a separate follow-up message after the option's
  digit keystroke, prefixed per the node-context rule below — it cannot be combined into
  the same keystroke as the option selection itself

#### Scenario: Every submission carries node context
- **WHEN** the user submits free text from any node's detail-pane input box (a plain
  reply box, a question node's "Other" field, or a question node's notes follow-up)
- **THEN** the text sent to the PTY is prefixed with a reference to that node's id and
  title — this does not apply to a question node's bare option-selection keystroke,
  which carries no text at all

### Requirement: Resolved-node document/artifact preview
The system SHALL let the user open a read-only preview of a node's linked local file
(a `decision` node's `doc`, or a `file`-kind `artifact` node's `path`) from that node's
detail pane, rendering the file's content without leaving the browser. A `url`-kind
`artifact` node SHALL instead render its `url` directly in an embedded iframe within the
detail pane (no separate preview panel), alongside a control to open that URL in a new
browser tab.

#### Scenario: Opening a node's linked file shows a preview
- **WHEN** the user selects a `decision` node with a `doc` field, or an `artifact`
  node, and activates its preview control in the detail pane
- **THEN** a preview panel renders that file's content

#### Scenario: Preview is read-only
- **WHEN** the document/artifact preview panel is open
- **THEN** it does not allow editing the underlying file from the GUI

#### Scenario: No preview action for nodes without a linked file
- **WHEN** the user clicks a `decision` node with no `doc` field, a `question` node, or
  an `info` node
- **THEN** no preview is shown for that node

#### Scenario: `url`-kind artifact embeds inline with an expand option
- **WHEN** the user selects a `url`-kind `artifact` node
- **THEN** its detail pane renders an iframe pointing at the node's `url`, plus a button
  that opens the same `url` in a new browser tab

#### Scenario: Private artifact shows claude.ai's own sign-in wall
- **WHEN** a `url`-kind `artifact` node's link has not been made publicly shared on
  claude.ai
- **THEN** the embedded iframe renders claude.ai's sign-in page rather than the artifact
  content — this is accepted, not treated as an error state by the GUI

### Requirement: Theme follows Claude Code's own light/dark setting
The GUI SHALL render in a dark or light visual theme matching the host's Claude Code
`theme` setting (`~/.claude/settings.json`), not the viewer's OS light/dark preference.
Both themes SHALL share the same monospace typography and token structure (background,
panel, border, foreground, dim text, accent) — only the token *values* differ. Both the
surrounding UI and the embedded terminal panel SHALL use the same resolved theme. When
the setting is missing, unreadable, or does not name a light theme, the GUI SHALL
default to the dark theme. The GUI SHALL also provide a manual override (auto/dark/light,
persisted client-side, e.g. `localStorage`) for when the backend's detection doesn't
match the user's actual environment; "auto" defers to the backend-detected theme.

#### Scenario: Dark theme is the default
- **WHEN** Claude Code's `theme` setting is unset, unreadable, or does not indicate a
  light theme
- **THEN** the GUI renders in the dark theme (background `#0a0c0b`, panel `#101211`,
  border `#242825`, foreground `#d7ddd4`, dim text `#5c655e`, accent `#9dff5c`)

#### Scenario: Light theme follows the config
- **WHEN** Claude Code's `theme` setting names a light theme
- **THEN** the GUI renders in the light theme, including the terminal panel's own color
  scheme, not just the surrounding UI

#### Scenario: Theme does not follow OS preference
- **WHEN** the viewer's operating system is set to light mode but Claude Code's own
  `theme` setting is dark (or unset)
- **THEN** the GUI still renders in the dark theme

#### Scenario: Manual override wins over backend detection
- **WHEN** the user sets the theme control to `dark` or `light` (not `auto`)
- **THEN** the GUI renders in that theme regardless of what the backend reported, and
  the choice survives a page reload

### Requirement: Optimistic pending indicator for in-flight submissions
The tree spine and detail pane SHALL visually distinguish a node whose submission was
just sent to the PTY from one that has not been interacted with, until the next
`tree:update` shows a change to that specific node. This state is local to the browser
tab — it is never written to `TREE.json` (per `Requirement: TREE.json is Claude-authored
structured data`); it exists only so the user has feedback that their input was received
before Claude has necessarily acted on and rewritten the tree.

#### Scenario: Node shows pending after submission
- **WHEN** the user submits an answer, reply, or option selection from a node's detail
  pane
- **THEN** that node is marked pending in both the spine and the detail pane immediately,
  before any `tree:update` message arrives

#### Scenario: Pending clears when that node's own data changes
- **WHEN** a `tree:update` arrives whose entry for the pending node differs from what it
  was at submission time (e.g. `status` or `answer`/`resolution` changed)
- **THEN** the pending indicator for that node clears

#### Scenario: Pending is not cleared by unrelated tree changes
- **WHEN** a `tree:update` arrives that changes other nodes but leaves the pending node's
  own data unchanged
- **THEN** the pending indicator for that node remains

### Requirement: Tree spine keyboard navigation
The tree spine SHALL support moving the selected node via keyboard, without requiring a
mouse click, using both vim-style keys and native arrow keys. This SHALL NOT intercept
these keys while focus is inside a text input or textarea in the detail pane, so typing
"j"/"k" into a reply box or notes field is never hijacked as navigation.

#### Scenario: Vim-style keys move the selection
- **WHEN** the tree spine has keyboard focus and the user presses `j` or `k`
- **THEN** the selected node moves to the next or previous node in the spine's visible
  (depth-first, expanded) order

#### Scenario: Arrow keys move the selection
- **WHEN** the tree spine has keyboard focus and the user presses the down or up arrow
  key
- **THEN** the selection moves the same way `j`/`k` does

#### Scenario: Navigation keys are inert while typing in the detail pane
- **WHEN** focus is inside a text input or textarea in the detail pane
- **THEN** `j`/`k`/arrow keys type their normal character/move the text cursor instead of
  changing the selected node

### Requirement: Question node keyboard quick-answer
When a `question` node is selected and the detail pane (not a text input within it) has
keyboard focus, number keys SHALL submit the corresponding option directly, and other
keys SHALL provide fast access to the "Other" and notes fields, without requiring a
mouse.

#### Scenario: Number key submits the corresponding option
- **WHEN** a `question` node is selected and the user presses a digit key `1`-`4`
  matching the position of one of its option cards
- **THEN** that option is submitted exactly as if its card had been clicked

#### Scenario: Selecting "Other" focuses its input
- **WHEN** the user activates the "Other" field (by keyboard or click)
- **THEN** keyboard focus moves to the "Other" text input immediately

#### Scenario: Enter submits, but not mid-IME-composition
- **WHEN** the "Other" field has focus and the user presses Enter
- **THEN** the field's content is submitted, UNLESS an IME composition is in progress (a
  composing Enter confirms the composed text instead of submitting)

#### Scenario: "n" focuses the notes field
- **WHEN** a `question` node's detail pane has focus (not inside a text input) and the
  user presses `n`
- **THEN** keyboard focus moves to the notes field
