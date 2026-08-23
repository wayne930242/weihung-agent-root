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
over the same WebSocket connection used for the session's message stream.

#### Scenario: Canvas updates without reload
- **WHEN** `TREE.json` changes on disk
- **THEN** the browser's canvas reflects the change without the user reloading the page

### Requirement: Node-graph canvas with a synthesized root card (design.md D12)
The GUI SHALL render as a single top-down node-graph canvas, not a split view — the
canvas is the primary and only main view. A root card, synthesized from the session's
`topic` (not a `TREE.json` node), SHALL always be present as the graph's top-level node,
so the discussion's own subject is visible without needing any `TREE.json` content yet.
Every `TREE.json` node SHALL render as its own card positioned beneath its `parent`
(falling back to the root card when `parent` is `null` or refers to an unknown id),
auto-laid-out top-down.

#### Scenario: Root card present before any TREE.json node exists
- **WHEN** the browser loads a session whose `TREE.json` has no nodes yet
- **THEN** the canvas still renders one card — the root card, showing the session topic

#### Scenario: New nodes position beneath their parent
- **WHEN** `TREE.json` gains a new node
- **THEN** a corresponding card appears on the canvas, connected by an edge from its
  parent card (or the root card, if it has no known parent)

#### Scenario: Empty tree renders without error
- **WHEN** `TREE.json` has no nodes yet (e.g. a session not using the tree at all)
- **THEN** the canvas renders just the root card, not an error

### Requirement: Per-type node rendering
The canvas SHALL render each node differently according to its `type`, so nodes of
different kinds are visually distinguishable.

#### Scenario: Distinct visual treatment per type
- **WHEN** the canvas renders nodes of different `type` values
- **THEN** each type's card reflects its distinct payload (e.g. a `decision` card shows
  its recommendation/resolution together, an `info` card shows its text, an `artifact`
  card shows an embed/preview affordance, a `question` card shows its prompt and options)

### Requirement: Node interaction sends a message into the session
Each card SHALL provide an interaction affordance (a free-text box; for a `question`-type
node, also clickable option cards, an "Other" free-text field, and a notes field)
appropriate to its type, always visible on that card — not gated behind a separate
selection step. Submitted text SHALL be pushed into the session's streaming input as a
plain message (`message:send`, `PROTOCOL.md`), prefixed with a reference to that node's
id and title, and SHALL NOT create a separate conversation channel.

#### Scenario: Text typed in a card reaches the session
- **WHEN** the user submits text from a card's free-text box
- **THEN** that text, prefixed with the node's id/title, is sent as a `message:send`

#### Scenario: Selecting a question option reaches the session
- **WHEN** the user clicks an option card on a `question`-type node's card
- **THEN** the option's label (plus any notes-field text), prefixed with the node's
  id/title, is sent as a `message:send`

#### Scenario: Custom reply on a question card
- **WHEN** the user types into the "Other" field on a `question`-type node's card
  instead of selecting an option
- **THEN** that text, prefixed with the node's id/title, is sent as a `message:send`

### Requirement: `#[id]`-tagged discussion routes to the node it's about (design.md D12)
The session's Claude SHALL prefix a reply with `#[node-id]` (the literal `id` of an
existing `TREE.json` node, at the very start of the message) when that reply discusses
one specific node; the GUI SHALL render such a reply nested in that node's own card
(beneath its ask/answer content) rather than on the root card, and SHALL strip the tag
from what's displayed. A message with no leading tag, or a leading tag whose id does not
match any node currently in the tree, SHALL render on the root card unmodified — the GUI
SHALL NOT treat a non-matching `#[...]`-shaped prefix as a routing mistake to silently
drop; it is displayed as ordinary text. The user's own submissions (`buildSubmission`)
use the same convention, so a card's own free-text/option submission is echoed on that
same card.

#### Scenario: Tagged reply nests under its node
- **WHEN** an assistant message starts with `#[node-id]` and `node-id` matches a node
  currently in `TREE.json`
- **THEN** the message (tag stripped) appears in that node's card, not the root card

#### Scenario: Untagged reply goes to the root card
- **WHEN** an assistant message has no leading `#[...]` tag
- **THEN** the message appears on the root card, unmodified

#### Scenario: Non-matching tag is left as plain text
- **WHEN** an assistant message starts with a `#[...]`-shaped prefix whose id does not
  match any node currently in `TREE.json`
- **THEN** the message appears on the root card with the prefix left in place, exactly as
  it would if there were no tag syntax involved at all

#### Scenario: A tag mid-message is not treated as a routing tag
- **WHEN** an assistant message contains `#[...]`-shaped text anywhere other than the
  very start
- **THEN** it is not treated as a routing tag and does not affect where the message
  renders

#### Scenario: Tool-use activity always renders on the root card
- **WHEN** the session's Claude calls a tool other than `AskUserQuestion`
- **THEN** the resulting card always appears on the root card's thread, never routed to
  a specific node — a tool call's input has no freeform text a tag could live in

#### Scenario: A card's own submission is echoed on that same card
- **WHEN** the user submits text from a specific node's card (its free-text box, an
  option pick, or an "Other" reply)
- **THEN** the echo of that submission appears on that same card, not the root card

### Requirement: Resolved-node document/artifact preview
The system SHALL let the user open a read-only preview of a node's linked local file
(a `decision` node's `doc`, or a `file`-kind `artifact` node's `path`) from that node's
card, rendering the file's content without leaving the browser. A `url`-kind `artifact`
node SHALL instead render its `url` directly in an embedded iframe within its card (no
separate preview panel), alongside a control to open that URL in a new browser tab.

#### Scenario: Opening a node's linked file shows a preview
- **WHEN** the user selects a `decision` node with a `doc` field, or an `artifact`
  node, and activates its preview control
- **THEN** a preview panel renders that file's content

#### Scenario: Preview is read-only
- **WHEN** the document/artifact preview panel is open
- **THEN** it does not allow editing the underlying file from the GUI

#### Scenario: No preview action for nodes without a linked file
- **WHEN** the user views a `decision` node with no `doc` field, a `question` node, or
  an `info` node
- **THEN** no preview is shown for that node

#### Scenario: `url`-kind artifact embeds inline with an expand option
- **WHEN** the user views a `url`-kind `artifact` node's card
- **THEN** it renders an iframe pointing at the node's `url`, plus a button that opens
  the same `url` in a new browser tab

#### Scenario: Private artifact shows claude.ai's own sign-in wall
- **WHEN** a `url`-kind `artifact` node's link has not been made publicly shared on
  claude.ai
- **THEN** the embedded iframe renders claude.ai's sign-in page rather than the artifact
  content — this is accepted, not treated as an error state by the GUI

### Requirement: Theme follows Claude Code's own light/dark setting
The GUI SHALL render in a dark or light visual theme matching the host's Claude Code
`theme` setting (`~/.claude/settings.json`), not the viewer's OS light/dark preference.
Both themes SHALL share the same monospace typography and token structure (background,
panel, border, foreground, dim text, accent) — only the token *values* differ, and both
SHALL meet WCAG AA contrast (4.5:1) for normal text. When the setting is missing,
unreadable, or does not name a light theme, the GUI SHALL default to the dark theme. The
GUI SHALL also provide a manual override (auto/dark/light, persisted client-side, e.g.
`localStorage`) for when the backend's detection doesn't match the user's actual
environment; "auto" defers to the backend-detected theme.

#### Scenario: Dark theme is the default
- **WHEN** Claude Code's `theme` setting is unset, unreadable, or does not indicate a
  light theme
- **THEN** the GUI renders in the dark theme (background `#0a0c0b`, panel `#101211`,
  border `#242825`, foreground `#d7ddd4`, dim text `#8a948d`, accent `#9dff5c`)

#### Scenario: Light theme follows the config
- **WHEN** Claude Code's `theme` setting names a light theme
- **THEN** the GUI renders in the light theme, including every card on the canvas, not
  just the surrounding chrome

#### Scenario: Theme does not follow OS preference
- **WHEN** the viewer's operating system is set to light mode but Claude Code's own
  `theme` setting is dark (or unset)
- **THEN** the GUI still renders in the dark theme

#### Scenario: Manual override wins over backend detection
- **WHEN** the user sets the theme control to `dark` or `light` (not `auto`)
- **THEN** the GUI renders in that theme regardless of what the backend reported, and
  the choice survives a page reload

### Requirement: Live AskUserQuestion answering in DetailSidebar
`AskUserQuestion` calls SHALL be detected the moment the tool is called (a single call
MAY carry 1-4 questions, each with 2-4 options and an optional `multiSelect` flag) — not
written to `TREE.json`. The call SHALL be attributed to the node card its first
question's text routes to (per the `#[id]` requirement above), or the root card if
untagged/unmatched: that card SHALL show a pending indicator, and the actual interactive
answering UI SHALL render in `DetailSidebar` once that card is focused — not inside the
card itself, which has no room for a multi-question call's full option set. Tool
execution SHALL remain blocked until the user answers, and the question SHALL stop
being treated as pending, on every connected browser, once answered.

#### Scenario: Pending indicator appears immediately
- **WHEN** the session's Claude calls `AskUserQuestion`
- **THEN** the attributed card shows a pending indicator within the same update cycle,
  before any corresponding `TREE.json` write (there is none)

#### Scenario: A browser connecting after the call still sees it
- **WHEN** a browser connects (or reconnects) while an `AskUserQuestion` call is still
  unanswered
- **THEN** the pending indicator (and, once that card is focused, the answering UI)
  appears on connect, not only to browsers that were already connected when the call
  fired

#### Scenario: A tagged question routes to its node
- **WHEN** an `AskUserQuestion` call's first question text starts with a `#[node-id]`
  tag matching a real node
- **THEN** the pending indicator and DetailSidebar answering UI attribute to that node's
  card, not root

#### Scenario: Every question's own tag is stripped for display
- **WHEN** more than one question in a single `AskUserQuestion` call starts with its own
  `#[node-id]` tag
- **THEN** each question's tag is stripped from its displayed text, even though only the
  first question's tag decides which card the whole call is attributed to

#### Scenario: A pending question auto-focuses its card, overriding drift
- **WHEN** a new `AskUserQuestion` call arrives
- **THEN** its attributed card becomes focused (and the viewport pans there), taking
  priority over whatever the user had been looking at — except an explicit action taken
  after that point (a click, `Tab`) can still move focus elsewhere

#### Scenario: Answering resolves the tool call and clears everywhere
- **WHEN** the user picks an option (or types free text) for every question and submits
  from DetailSidebar
- **THEN** the answers are sent as `question:answer`, the session's blocked tool call
  resolves, the conversation continues, and every connected browser (not only the one
  that answered) stops showing that question as pending

#### Scenario: Multi-select question collects multiple picks
- **WHEN** a question's `multiSelect` is true
- **THEN** the user can pick more than one option before submitting, and all picks are
  included for that question in the submitted answer

### Requirement: Reconsidering a resolved node flips its status immediately, then asks Claude to reconcile
A resolved `decision` or `question` node's card SHALL provide a "重新考慮" control that
(a) has the backend flip that node's `status` back to `open` directly in `TREE.json` —
a narrow, program-driven exception to Claude being the sole author, scoped to this one
field (design.md D12) — and (b) sends Claude a follow-up message naming the node (by id
and title) and asking it to reconcile anything that depended on it. This is a new
forward turn for the session's own conversation, not a rollback — an already-answered
`AskUserQuestion` in the transcript is not affected, only what the session's Claude
subsequently writes to `TREE.json`. This control is NOT offered on a live
`AskUserQuestion` card: an answered tool call cannot be un-sent, only a persisted
`TREE.json` node can actually be rewritten.

#### Scenario: Reconsider flips status before Claude responds
- **WHEN** the user activates a resolved `decision` or `question` node's "重新考慮"
  control
- **THEN** that node's `status` becomes `open` in `TREE.json` immediately (an atomic
  write, not waiting on a Claude turn), and a message asking Claude to reconcile
  dependent nodes is sent

#### Scenario: Not offered on open nodes or other types
- **WHEN** a node is `open`, or is an `artifact`/`info` node
- **THEN** no "重新考慮" control is shown for it

#### Scenario: Not offered on live AskUserQuestion cards
- **WHEN** the user views an already-answered `AskUserQuestion` card
- **THEN** no retract/reconsider control is offered there — only the equivalent control
  on a `TREE.json` node, if the interview promoted that decision into one

### Requirement: Explicit session controls in fixed chrome, not on a canvas card
A navigation bar (topic, `TREE.json` status, theme control, finalize, stop) and a
general-purpose message input SHALL be fixed chrome outside the pannable canvas, not
rendered as, or inside, a graph node — a control that's part of the graph isn't
reliably reachable once the viewport has panned or zoomed elsewhere. The finalize
("定案") control SHALL ask Claude to wrap up now (resolve/drop every open branch, write
the summary doc, set `TREE.json`'s top-level `status` to `complete`) without waiting for
Claude to decide to ask first; the stop control SHALL stop the session immediately. Both
are explicit user actions, not inferred task-completion — the same category as the two
mechanical exceptions to "never shut down" (`open-gui-session`), not a reversal of that
rule.

#### Scenario: Session controls stay reachable regardless of viewport position
- **WHEN** the user has panned or zoomed the canvas away from any particular card
- **THEN** the finalize, stop, theme, and message-input controls remain visible and
  usable, since none of them are canvas nodes

#### Scenario: Finalize control sends a direct instruction
- **WHEN** the user activates the finalize ("定案") control
- **THEN** a message asking Claude to resolve/drop every open branch, write the summary
  doc, and set `TREE.json` status to `complete` is sent — without requiring Claude to
  have already called `AskUserQuestion` to confirm first

#### Scenario: Stop control shuts the backend down
- **WHEN** the user activates the stop control
- **THEN** the backend shuts itself down immediately, the same as it would for an
  external `SIGTERM`

#### Scenario: A message from the general input is untagged
- **WHEN** the user sends a message from the fixed chat input (not a specific card's own
  reply box)
- **THEN** it carries no node-id prefix and renders on the root card, like any other
  untagged content

### Requirement: Cards show only their latest entry; DetailSidebar shows the rest
Each canvas card SHALL render at most its own ask/answer content (recommendation/
resolution, prompt/options, artifact embed, info text, as applicable) plus only the
single most recent thread entry routed to it — not its full history. `DetailSidebar`
SHALL render the full thread for whichever card is currently focused.

#### Scenario: A card shows just the latest entry
- **WHEN** more than one thread entry has routed to a given card
- **THEN** the card itself displays only the most recent one

#### Scenario: Focusing a card reveals its full history
- **WHEN** the user focuses a card (by click or keyboard)
- **THEN** `DetailSidebar` renders every entry routed to that card, in order, not just
  the latest

### Requirement: Cards size to their content, not a fixed pixel height
A card SHALL grow to fit its content up to a maximum height (beyond which it scrolls
internally), rather than being a fixed pixel size that can clip content. The layout
engine's per-node size figure used for graph spacing is an estimate for that purpose
only, not a promise the rendered card matches it exactly.

#### Scenario: Long recommendation/resolution text is not clipped
- **WHEN** a card's recommendation, resolution, or prompt text is long enough that a
  small fixed card would have cut it off
- **THEN** the card grows taller to show it, up to the maximum height

#### Scenario: Graph spacing tolerates cards of different actual heights
- **WHEN** two sibling cards end up with different actual rendered heights
- **THEN** the graph still lays out without cards overlapping, even though the spacing
  estimate doesn't exactly match either card's real height

### Requirement: Click-to-focus and keyboard navigation across cards
Clicking any card SHALL focus it (panning the viewport there and showing its full
history in `DetailSidebar`). `Tab`/`Shift+Tab`, when focus is not inside a text input,
SHALL cycle focus forward/backward through cards that need action — a live pending
question, or a persisted `question`-type node still `open`. While a card is focused:
digit keys `1`-`4` SHALL pick and submit the corresponding option, but only when exactly
one question is pending (a multi-question call has no single unambiguous option list for
a bare digit to mean, so this is mouse-only there); `/` SHALL focus that card's own
reply/Other input; `n` SHALL focus its notes field where one exists; `:` SHALL always
focus the general message input regardless of which card is focused.

#### Scenario: Clicking a card focuses it
- **WHEN** the user clicks anywhere on a card
- **THEN** that card becomes focused, the viewport pans to it, and `DetailSidebar`
  updates to show its full history

#### Scenario: Tab cycles through actionable cards only
- **WHEN** the user presses `Tab` (or `Shift+Tab`) outside any text input
- **THEN** focus moves to the next (or previous) card with a live pending question or an
  open `question`-type node, skipping cards that need no action

#### Scenario: Digit key answers a single pending question
- **WHEN** the focused card has exactly one pending question and the user presses a
  digit key matching one of its options
- **THEN** that option is submitted immediately, as if clicked

#### Scenario: Digit keys are inert for a multi-question call
- **WHEN** the focused card's pending question is a multi-question call
- **THEN** digit keys do not submit anything — answering there is mouse-only

#### Scenario: An explicit focus action can look away from a pending question
- **WHEN** a question is pending on one card and the user explicitly clicks or Tabs to a
  different card
- **THEN** focus moves as requested, even though a question is still unanswered
  elsewhere
