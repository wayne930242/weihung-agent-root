---
name: open-gui
description: Use when the user wants a browser-based GUI for a Claude Code session — "open a GUI", "browser terminal", "web version of claude", or a live decision-tree panel alongside the conversation. Also the dependency other skills reach for when they need a session running in a browser (e.g. grill-with-web) — invoke it with a seed prompt and topic rather than reimplementing PTY/browser plumbing.
---

# open-gui

Spin up a fresh, independent `claude` session driven through the Agent SDK, with a card-based conversation pane and a live typed-node tree panel beside it (design.md D11). `AskUserQuestion` calls render as live interactive cards and are answered structurally — no terminal, no keystroke emulation.

**Passive by default.** Once launched, do not poll it, do not wait for it, do not close it. The session runs until the user or a calling skill stops it. This is the one rule every step below exists to protect — read [Passive lifecycle](#passive-lifecycle) before you do anything that looks like waiting.

## 1. First-run setup

Run `skills/open-gui/init.sh` (macOS/Linux) or `skills/open-gui/init.ps1` (Windows — best-effort, unverified on a real Windows machine). It's idempotent: installs Deno if missing, checks for Node.js (needed only for the frontend's own build tooling — the backend itself is pure Deno, including the Agent SDK via an `npm:` specifier), and builds the frontend — each step skipped if already done.

## 2. Determine session parameters

- `cwd`: the target project root. Default to the current working directory unless told otherwise.
- `topic`: a short label for the session (shown in the browser). Derive from what the user asked for; default to `"open-gui session"` if nothing specific was said.
- `seed prompt` (optional): only construct one if there's real content to seed the new session with — a topic, background, relevant file paths, or (when invoked by another skill) that skill's own seed-prompt contract. An empty/trivial seed prompt is worse than none — the new session opens to its normal empty prompt instead.
- `session-id`: generate one (e.g. a short random id). Choosing it yourself (rather than
  omitting `--session-id` and letting the backend generate one) is what makes the state
  directory path predictable *before* launch — see below if your seed prompt needs to
  reference `TREE.json`.

## 3. Launch the backend

If a seed prompt was determined, write it to a temp file. From `skills/open-gui/server/`, start the backend as a **background process**:

```
deno run --allow-net --allow-read --allow-write --allow-run --allow-env --allow-sys main.ts \
  --cwd <cwd> --topic <topic> --session-id <session-id> [--seed-file <path>]
```

Read the backend's output (or poll `~/.claude/state/<project-slug>/open-gui/<session-id>/session.json` a few times with short waits) for the assigned URL — the backend prints `session ready: <url>` once `Deno.serve` has bound its port. Don't guess the port; it's OS-assigned.

## 4. Open the browser

Attempt to auto-open the user's default browser to the session URL, **bringing it to the foreground** — not just launching it in a background tab the user has to go find. Use the platform's own opener: `open <url>` (macOS), `xdg-open <url>` (Linux), `start <url>` via `cmd /c start "" <url>` (Windows) — all three activate the target app, no extra focus step needed. If you're on a platform/method where opening doesn't focus the window, bring it forward as a separate step. The point is the user sees the session the moment it's ready, without hunting for it. **Always print the full URL regardless of whether auto-open succeeds** — auto-open is unreliable in some environments (e.g. WSL) and silent failure there would strand the user with no way to reach the session.

## 5. Report and stop

Tell the user the session is running, give them the URL, and state plainly that it stays open — you are not going to check back on it or close it. Point at `~/.claude/state/<project-slug>/open-gui/<session-id>/session.json` (`pid`, `port`) as how they (or you, if later asked) can stop it: send that PID `SIGTERM`, which closes the Agent SDK session (and the `claude` subprocess it spawned) before exiting.

Your turn ends here. Do not add a step that waits for the interview/task inside the session to finish.

## Switch to a normal terminal

Closing the browser tab does **not** immediately pause or hand anything back — the session keeps running server-side and reopening the URL reconnects to it right away. A closed WebSocket isn't a reliable "the user is done" signal (indistinguishable from an accidental close or a network blip), so nothing here triggers automatically on disconnect. It's also not permanent: see [Passive lifecycle](#passive-lifecycle)'s idle-shutdown note — a tab left closed for a sustained period does eventually stop the backend, as a resource-hygiene measure, not a hand-off.

If the user explicitly wants to keep going in an ordinary terminal instead of the browser: the spawned `claude` process was started with a pinned `--session-id` (recorded as `claudeSessionId` in `session.json`, also printed to the backend's own log at startup) specifically so this is possible. Stop this open-gui session first (§5) — the same session must not be open in two places at once, for the same JSONL-corruption reasons D1 rules out resuming the *invoking* session — then the user (or you, if asked) runs:

```
claude --resume <claudeSessionId>
```

This resumes the *same* session's own transcript in a plain terminal, picking up exactly where the browser left off. It is not the same thing as resuming the session that originally invoked `open-gui` — that's still never done (D1).

## Passive lifecycle

`open-gui` never reads `TREE.json`'s completion status, never polls, never infers "done" from task content. That is deliberate (design.md D8/D9) — a general-purpose browser-GUI tool that auto-closes sessions the user might still be using is worse than one that just runs until told to stop. If a task needs "wait for completion, then clean up," that behavior belongs in the *calling* skill (see below), layered on top — not here.

**Two exceptions, both mechanical rather than task-completion judgment calls:** the backend shuts itself down if the session stream ends on its own (the wrapped `claude` process exited, or the SDK session hit a fatal error — see `PROTOCOL.md`'s `session:ended`), and if zero browsers have been connected for 15 minutes straight (a forgotten tab, or an auto-open that silently failed and nobody ever opened the URL — otherwise it would run forever unattended). Any connection within that 15-minute window cancels the timer, so a quick reconnect after an accidental close is unaffected.

## For other skills invoking open-gui

Invoke `open-gui` with your seed prompt and topic instead of reimplementing PTY/WebSocket/browser plumbing. What you get back:

- The session's state directory: `~/.claude/state/<project-slug>/open-gui/<session-id>/`, containing `TREE.json` (poll its top-level `status` for your own completion detection — `NODE-FORMAT.md` documents the schema) and `session.json` (`pid`/`port`/`url` — use the `pid` to stop the backend yourself when you're done; `open-gui` will not do it for you). `project-slug` is `server/state.ts`'s `projectSlug(cwd)`: the target `cwd`'s basename, lowercased, with every run of non-alphanumeric characters collapsed to a single hyphen (leading/trailing hyphens trimmed).
- **The target session has no way to discover this path on its own** — it isn't passed as an env var, and the `--session-id` the spawned `claude` process itself gets (`claudeSessionId` in `session.json`) is a *different* id from the one that determines this directory. Since you chose `session-id` yourself in step 2, you can compute the full path (`.../TREE.json`) before writing the seed prompt — **include that literal absolute path in the seed prompt text**, not just a reference to `NODE-FORMAT.md`'s schema, or the target session has nothing to write to.
- Your seed prompt should get the target session populating that `TREE.json` path using the node types in `NODE-FORMAT.md`, and setting top-level `status` to `complete` when its task is done (that's your completion signal, not anything `open-gui` provides) — **read `NODE-FORMAT.md` yourself and write the relevant node shapes directly into the seed prompt text, don't just tell the target session to "use NODE-FORMAT.md."** The target session starts with nothing loaded; a bare path reference makes it spend its own first turn discovering the file (observed: 30s+ and a failed background search) instead of starting the actual task. It should never need a tool call just to find out how to behave.

See `PROTOCOL.md` if you need the wire-level detail (you shouldn't for a normal invocation — the state directory is the actual interface).
