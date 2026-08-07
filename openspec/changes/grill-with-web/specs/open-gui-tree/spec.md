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
The GUI SHALL display the chat/transcript panel and the tree panel simultaneously in a
resizable split view by default, and SHALL NOT hide or collapse the tree panel by
default, regardless of whether any nodes have been written yet.

#### Scenario: Both panels visible on load
- **WHEN** the browser loads the session page
- **THEN** both the chat/transcript panel and the tree panel are visible without
  requiring additional user action

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

### Requirement: Node interaction sends a message into the session
The tree panel SHALL render as a master/detail pair: a compact spine listing every node
as one row, and a detail pane showing the full content of whichever node is currently
selected. Interaction affordances (reply boxes, option cards, the "Other" field, the
notes field) SHALL render only in the detail pane for the selected node, not inline for
every node at once. Each node SHALL provide an interaction affordance whose submitted
text is pushed into the session's streaming input as a plain message (`message:send`,
`PROTOCOL.md`), and SHALL NOT create a separate conversation channel. `question`-type
nodes (a `TREE.json`-persisted question from a non-`grill-with-web` consumer — see
`NODE-FORMAT.md`'s D11 note) SHALL render clickable option cards, an "Other" free-text
field, and a notes field; other node types SHALL render a plain free-text box where
applicable. Every submission SHALL be prefixed with a reference to that node's id and
title, so the session can identify which node is being answered even when multiple nodes
are open at once.

design.md D11 superseded the previous PTY-based version of this requirement (raw-mode
menu digit keystrokes, paste-detection timing): a plain streamed message carries no
terminal-input ambiguity, so option selections, "Other" replies, and notes are now a
single ordinary text submission each — no multi-step keystroke sequence, no staleness
risk about "what's currently on screen" (there is no screen to be stale against).

#### Scenario: Text typed in a node reaches the session
- **WHEN** the user selects a node in the spine and submits text from its detail pane's
  input box
- **THEN** that text, prefixed with the node's id/title, is sent as a `message:send`

#### Scenario: Selecting a question option reaches the session
- **WHEN** the user selects a `question` node in the spine and clicks an option card in
  its detail pane
- **THEN** the option's label (plus any notes-field text), prefixed with the node's
  id/title, is sent as a `message:send`

#### Scenario: Custom reply on a question node
- **WHEN** the user types into the "Other" field in a `question` node's detail pane
  instead of selecting an option
- **THEN** that text, prefixed with the node's id/title, is sent as a `message:send`

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
panel, border, foreground, dim text, accent) — only the token *values* differ. When
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
- **THEN** the GUI renders in the light theme, including the chat/transcript panel, not
  just the surrounding UI

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
just sent to the session from one that has not been interacted with, until the next
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

### Requirement: Card-based transcript pane (design.md D11)
The chat/transcript panel SHALL render the session's message stream as a list of
discrete cards (assistant text, one-line tool-call summaries, system records), not raw
terminal text, and SHALL provide a free-text input for sending new messages into the
session.

#### Scenario: Assistant text renders as a card
- **WHEN** the session emits assistant text
- **THEN** it appears as its own card, rendered as markdown

#### Scenario: A tool call renders as a one-line summary card
- **WHEN** the session's Claude calls a tool other than `AskUserQuestion`
- **THEN** a card appears naming the tool and a short summary of its input — not full
  tool-result content

#### Scenario: Free-text input sends a message
- **WHEN** the user types into the transcript pane's input box and submits
- **THEN** that text is sent as a `message:send`, with no node-context prefix

### Requirement: Live AskUserQuestion answering
`AskUserQuestion` calls SHALL render as an interactive card in the transcript pane at
the moment the tool is called, addressing every question in that call (a single
`AskUserQuestion` call MAY carry 1-4 questions, each with 2-4 options and an optional
`multiSelect` flag) — not written to `TREE.json` and not requiring a page reload to
appear. Tool execution SHALL remain blocked until the user answers.

#### Scenario: Question card appears immediately
- **WHEN** the session's Claude calls `AskUserQuestion`
- **THEN** a question card appears in the transcript pane within the same update cycle,
  before any corresponding `TREE.json` write (there is none)

#### Scenario: A browser connecting after the call still sees it
- **WHEN** a browser connects (or reconnects) while an `AskUserQuestion` call is still
  unanswered
- **THEN** the pending question card appears on connect, not only to browsers that were
  already connected when the call fired

#### Scenario: Answering resolves the tool call
- **WHEN** the user picks an option (or types free text) for every question in the card
  and submits
- **THEN** the answers are sent as `question:answer`, the session's blocked tool call
  resolves, and the conversation continues

#### Scenario: Multi-select question collects multiple picks
- **WHEN** a question's `multiSelect` is true
- **THEN** the user can pick more than one option before submitting, and all picks are
  included for that question in the submitted answer

### Requirement: Promote a transcript card into a tree node
A card in the transcript pane (assistant text or a tool-call summary) SHALL provide a
control that asks the session's Claude to add a corresponding `TREE.json` node, without
the frontend writing to `TREE.json` directly — `TREE.json` remains Claude-authored only
(`Requirement: TREE.json is Claude-authored structured data`, `open-gui-session`).

#### Scenario: Promoting a card sends a message, not a file write
- **WHEN** the user activates a card's "加進 tree" control
- **THEN** a `message:send` asking Claude to add a node for that card's content is sent;
  no `TREE.json` write happens directly from the browser

#### Scenario: Promote control is not offered on system cards
- **WHEN** a transcript entry is a system-kind record (an echoed user message, an
  "Answered: …" record)
- **THEN** it does not offer a "加進 tree" control

### Requirement: Reconsider a resolved tree node
A resolved `decision` or `question` node's detail pane SHALL provide a control that asks
the session's Claude to reopen that node and update or remove anything in `TREE.json`
that depended on it. This is a new forward turn, not a rollback — it does not remove or
alter the node's prior resolution/answer in the session's own conversation history, only
what the session's Claude subsequently writes to `TREE.json`. This control is
intentionally not offered on the transcript pane's `AskUserQuestion` cards: an answered
tool call cannot be un-sent, only a persisted `TREE.json` node can actually be rewritten.

#### Scenario: Reconsider sends a message, not a rollback
- **WHEN** the user activates a resolved `decision` or `question` node's "重新考慮"
  control
- **THEN** a `message:send` asking Claude to reopen that node (by id and title) and
  reconcile dependent nodes is sent

#### Scenario: Not offered on open nodes or other types
- **WHEN** a node is `open`, or is an `artifact`/`info` node
- **THEN** no "重新考慮" control is shown for it

#### Scenario: Not offered on transcript question cards
- **WHEN** the user views an already-answered `AskUserQuestion` card in the transcript
  pane
- **THEN** no retract/reconsider control is offered there — only the equivalent control
  on a `TREE.json` node, if the interview promoted that decision into one
