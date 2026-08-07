# open-gui wire protocol

design.md D11: the backend drives each session through `@anthropic-ai/claude-agent-sdk`'s
`query()` directly (a Deno `npm:` specifier) — no PTY, no Node.js sidecar, no IPC hop.
There is exactly one wire protocol left: the browser WebSocket. JSON text frames only.

## Browser WebSocket (browser ↔ Deno)

One WebSocket connection per browser tab. Multiplexes the transcript feed, live
`AskUserQuestion` answering, tree push, and doc/artifact preview.

**Browser → Deno:**

| `type`             | fields                          | meaning                                                                 |
|---------------------|-----------------------------------|---------------------------------------------------------------------------|
| `message:send`      | `text` (string)                   | a free-text message to push into the session's streaming input — the transcript pane's own input box, a node's `FreeTextBox`, a tree node's "重新考慮"/reconsider action, and a chat card's "加進 tree" promote action all funnel through this one message type |
| `question:answer`   | `requestId`, `answers`            | answers a pending `question:ask` — `requestId` is the `canUseTool` call's `toolUseID` this answers, `answers` is `{[question text]: selected label(s)}`, matching the Agent SDK's expected `AskUserQuestion` response shape |
| `preview:request`   | `requestId`, `path`               | request a local file's contents for the read-only preview panel          |

**Deno → browser:**

| `type`               | fields                                  | meaning                                                                 |
|-----------------------|-------------------------------------------|---------------------------------------------------------------------------|
| `config`              | `theme` (`"dark"` \| `"light"`)           | sent once, immediately on connect: the host's Claude Code theme preference (best-effort read of `~/.claude/settings.json`, default `"dark"` — design.md D7 revision) |
| `transcript:snapshot` | `entries[]`                               | sent once, immediately on connect: every buffered transcript entry since spawn (bounded ring buffer, last 2000), so a (re)connecting browser sees history before live events resume |
| `transcript:event`    | `entry`                                   | one new transcript entry — `{kind: "assistant", text}`, `{kind: "tool_use", tool, summary}`, or `{kind: "system", text}` (promote-to-tree echoes, "Answered: …" records) |
| `question:ask`        | `requestId`, `questions[]`                | `AskUserQuestion` was called and is blocked waiting for an answer — `questions[]` is the SDK's own structure (`question`, `header`, `options[]` with `label`/`description`, `multiSelect`). Also (re)sent immediately on connect if a question is still pending, so a browser connecting *after* the call already fired still sees it |
| `tree:update`         | `tree` (full `TREE.json` contents)        | sent once immediately on connect with current state, then again on every `TREE.json` change — always the full document, never a diff (the file is small; diffing isn't worth the complexity) |
| `preview:response`    | `requestId`, `content` or `error`         | response to a `preview:request`                                          |
| `fatal`               | `message`                                 | an unrecoverable backend error (the SDK session stream threw) — the browser SHOULD render this prominently |
| `session:ended`       | *(no fields)*                             | the session stream ended (process exit or a fatal error) — the backend broadcasts this and then shuts itself down (~500ms later); the browser SHOULD render this distinctly from `fatal` (not necessarily an error — the session may have ended intentionally) |

**Why no `pty:resize`:** there's no terminal to resize — the transcript pane is a
scrolling card list, sized by ordinary CSS layout, not a fixed-grid PTY.

**AskUserQuestion answering, mechanically (design.md D11):** the backend's `canUseTool`
callback blocks on a `Promise` when `toolName === "AskUserQuestion"`, keyed by the SDK's
own `toolUseID`. `question:ask` broadcasts the payload immediately; the promise resolves
when a matching `question:answer` arrives, which is what lets the SDK's session turn
continue. Verified live: the callback stays correctly pending across a real multi-second
wait with no timeout, and the underlying connection stays alive during it (confirmed via a
`rate_limit_event` arriving mid-wait in the spike that validated this design).

**Transcript buffering for reconnect:** the Deno process keeps an in-memory ring buffer of
transcript entries (bounded — last 2000), independent of any WebSocket connection state.
This is what `transcript:snapshot` replays on (re)connect.

**Idle shutdown:** independent of `session:ended`, the backend also shuts itself down (no
broadcast — by definition nobody is connected) after 15 minutes with zero open WebSocket
connections, whether that's because every tab was closed or because the browser never
connected in the first place (e.g. auto-open silently failed). Any new connection within
that window cancels the timer.

**Seed prompt delivery:** the seed prompt is simply the first message pushed into the
session's streaming input generator, at process startup — there is no PTY-readiness race
to wait out (D11 removed the PTY entirely), and no paste-detection to work around (a
streamed `SDKUserMessage` is not typed keystrokes, so nothing can mistake it for a paste).
