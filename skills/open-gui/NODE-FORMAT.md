# `TREE.json` node format

`TREE.json` lives in the session's state directory
(`~/.claude/state/<project-slug>/open-gui/<session-id>/TREE.json`). The session's
`claude` process is responsible for writing it — this file is never inferred from the
PTY transcript (design.md D4).

## Top level

```json
{
  "topic": "string — short label for the session, shown in the browser tab/header",
  "status": "in_progress | complete",
  "nodes": [ /* Node[], see below */ ]
}
```

`status` starts `in_progress`. Setting it to `complete` is how a session signals it is
done — `open-gui` itself never reads this field (it is fully passive, design.md D8/D9);
a consumer skill like `grill-with-web` polls it.

## Base node shape

Every node has these fields, plus a `type`-specific payload merged in:

```json
{
  "id": "string, unique within the tree",
  "type": "decision | question | artifact | info",
  "parent": "string (another node's id) | null — null for a root node",
  "title": "string — short label shown in the tree UI"
}
```

## `decision`

A branch that resolves to a specific recommendation/decision.

```json
{
  "recommendation": "string — the proposed direction, shown while open",
  "status": "open | resolved",
  "resolution": "string — required once status is resolved; the actual decision made",
  "doc": "string, optional — local file path (e.g. an ADR) for the read-only preview panel"
}
```

- `resolution` MUST be present when `status` is `resolved`, and MUST be absent/omitted
  while `open`.
- `doc` is optional at any status — not every decision produces a linked document.

## `question`

An open question, rendered with clickable option cards. The UI always additionally
renders an "Other" free-text field and a notes field alongside whatever options are
listed — mirroring the `AskUserQuestion` tool's own interface (custom replies and
per-selection notes are core to that tool, not edge cases to omit here).

**design.md D11:** `grill-with-web` no longer writes this node type — its
`AskUserQuestion` calls are answered live, through the transcript pane's own
`question:ask`/`question:answer` flow (`PROTOCOL.md`), which is both faster (no lag
waiting for a `TREE.json` write) and avoids showing the same question twice. This type
stays valid in the schema for other `open-gui` consumers that want a persisted,
tree-navigable question instead of (or in addition to) a live one.

```json
{
  "prompt": "string — the question text",
  "options": [
    { "label": "string", "description": "string, optional" }
  ],
  "status": "open | resolved",
  "answer": {
    "selectedLabel": "string, optional — set if an option card was clicked",
    "customText": "string, optional — set if answered via the \"Other\" field instead",
    "notes": "string, optional — free-text notes attached to the answer"
  }
}
```

- `answer` MUST be present when `status` is `resolved`, with at least one of
  `selectedLabel`/`customText` set. Both may be set (an option chosen, refined by
  notes) but `selectedLabel` and `customText` are not both meant to carry conflicting
  primary answers — `customText` alone means "Other" was used instead of any option.
- `options` MAY be an empty array (a free-text-only question); the "Other" field and
  notes field still render in that case.

## `artifact`

Embeds/previews either a local file or a published `claude.ai` artifact, selected by
`kind` (default `"file"`).

```json
{
  "kind": "file | url — optional, defaults to \"file\"",
  "path": "string — required when kind is \"file\": local file path, relative to the target project root",
  "url": "string — required when kind is \"url\": a claude.ai artifact link",
  "caption": "string, optional"
}
```

- `kind: "file"` (or omitted) reuses the same read-only preview mechanism as
  `decision`'s `doc` field (`PROTOCOL.md`'s `preview:request`/`preview:response` — one
  code path, not two).
- `kind: "url"` renders the URL directly in an iframe, plus an "Open in new tab" button.
  `claude.ai` artifacts are private by default — an iframe for one that hasn't been
  shared publicly will show `claude.ai`'s own sign-in wall instead of the artifact
  content. This is accepted: the caller (or the user) is responsible for using a
  public/shared link if inline viewing matters, and "Open in new tab" still gets the
  user to a working sign-in flow either way.
- `path` and `url` are mutually exclusive — exactly one is present, matching `kind`.

## `info`

Static, non-interactive context.

```json
{
  "text": "string — markdown content"
}
```

## Validation rules (for the schema test, Task 4.2)

- `id` is unique across `nodes`.
- `parent`, if not `null`, refers to an existing node's `id`.
- `type` is one of the four values above; the matching payload fields are present and
  fields belonging to other types are absent.
- For `decision`/`question`: `status` is `open` or `resolved`; the resolution field
  (`resolution`/`answer` respectively) is present if and only if `status` is `resolved`.
- `artifact`/`info` have no `status` field — they are not open/resolved concepts.
