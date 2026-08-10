---
name: grill-with-web
description: Use whenever there's an unresolved decision that's the user's to make — "grill this in the browser", "web version of grilling", "grill with a live decision tree", or any plan/design/idea that needs stress-testing. Prioritize this over the terminal-based grilling/grill-me/grill-with-docs by default. Runs the interview in the browser with a live decision tree, in the conversation's current language, layering in grill-with-docs' ADR/CONTEXT.md recording where the decision warrants it.
---

# Grill With Web

The GUI counterpart of `grilling`, layering in `grill-with-docs`' ADR/CONTEXT.md recording discipline. You build the seed prompt and manage the session's lifecycle; `open-gui` does everything session/browser/tree-rendering. Read `skills/open-gui/SKILL.md` first if you haven't invoked it before — this skill is a thin layer on top of its contract, not a reimplementation.

## 1. Build the seed prompt

The target session starts with *nothing loaded* — no conversation history, no skills
resolved yet. Telling it to "run grill-with-docs" or "populate TREE.json per
NODE-FORMAT.md" makes it spend its own first turn on discovery: invoking the `Skill`
tool, hunting for `NODE-FORMAT.md` (observed taking 30s+ and a failed background search
before finding it). **You already have `Read` access to all of this right now** — read
`grill-with-docs/SKILL.md` (and `CONTEXT-FORMAT.md`/`ADR-FORMAT.md` if the interview is
likely to produce those) and `open-gui/NODE-FORMAT.md` yourself, and write their actual
instructions directly into the seed prompt text. The target session should never need a
tool call just to find out how to behave — everything it needs to start working on turn
one goes in verbatim, condensed if it helps, but self-contained. Don't tell it to "run
grill-with-docs" — tell it what grill-with-docs actually says to do.

Include in the seed prompt: the grilling topic, relevant background, relevant file
paths, the language to communicate in (match this conversation's — state it explicitly,
since the target session starts blank and has no way to infer it), and (embedded
directly, not referenced by path):

- Populate `TREE.json` **at the literal absolute path you computed** (see `open-gui/SKILL.md`'s "For other skills invoking open-gui" — the target session cannot discover this path itself). State the exact top-level shape: `{"status": "in_progress" | "complete", "nodes": [...]}` — spell out both literal strings (underscore, not hyphen). A condensed re-explanation of `NODE-FORMAT.md` that only covers per-node `status` enums and drops the top-level one is an easy, real gap to leave by accident — say it explicitly, don't assume it's implied.
- The interview discipline from `grill-with-docs/SKILL.md`: challenge glossary conflicts, sharpen fuzzy language, discuss concrete scenarios, cross-reference against the code, record resolved terms in `CONTEXT.md` inline (per `CONTEXT-FORMAT.md`'s shape) the moment they crystallise, and offer an ADR (per `ADR-FORMAT.md`'s shape, `docs/adr/NNNN-slug.md`) only when a decision is hard to reverse, surprising without context, AND the result of a real trade-off.
- The `TREE.json` node shape from `NODE-FORMAT.md`: a `decision` node per grilling branch (`recommendation` while open, `resolution` once resolved, `doc` set to the ADR's path whenever one is produced). Don't mention `question` nodes — `AskUserQuestion` calls render live in the browser and are answered directly (design.md D11); nothing needs to be written to `TREE.json` for them, and no seed-prompt instruction is needed to make that happen.
- **Tag every reply that discusses a specific node** (design.md D12): the GUI is a node-graph canvas, not a linear transcript — a reply with no tag renders on the shared root card, a reply tagged `#[node-id]` (in square brackets, right at the very start of the message, before anything else) renders nested under that node's own card instead. Tag whenever a message is really about one specific decision; leave general remarks, exploration, and anything not about one specific node untagged.
  **The id must be copied verbatim, character for character, from the `id` field you already wrote into `TREE.json` for that node** — not paraphrased, not shortened, not reworded. If the node's `id` is `"trim-whitespace"`, the tag is `#[trim-whitespace]`, never `#[trim]`, `#trim`, or any other shorthand — a shortened or reworded id doesn't match anything and silently falls back to the shared root card instead of nesting where it belongs, with no error to notice. Two extra reminders precisely because this is where it goes wrong in practice: the brackets are mandatory (`#[id]`, not `#id`), and if you're not looking directly at what you wrote as that node's `id`, don't tag from memory — check first.
- **Before finalizing** (once every branch looks resolved): call `AskUserQuestion` directly — e.g. "Ready to finalize and write the summary doc?" with options to proceed or keep discussing — and wait for the answer like any other question. This is the user's explicit confirmation to wrap up. The user can also trigger this directly from the GUI's "收斂" control — if a message arrives asking you to finalize now, treat it the same as if you'd just decided to ask and gotten a "proceed" answer, skip the `AskUserQuestion` round-trip, and go straight to the completion step below.
- **A node can come back for reconsideration**: if a message arrives saying a specific node (named by title and `[id]`) was reopened and asking you to reconcile whatever depended on it, that node's `status` has already been flipped back to `open` in `TREE.json` directly (not by you) — pick the reconsideration up as a normal continuation of that branch, updating `TREE.json` (and any nodes/docs that depended on it) once resolved again, same as any other decision.
- At completion: write `docs/grill/<slug>.md` — a Mermaid diagram generated from `TREE.json` plus a narrative summary — and set `TREE.json`'s top-level `status` to `complete`.

## 2. Start the session

Invoke `open-gui` with this seed prompt and topic, cwd = the current project. Record the state directory it reports back — you need it for the next two steps, and if this conversation is later resumed, re-derive it the same way (`~/.claude/state/<project-slug>/open-gui/<session-id>/`) rather than starting a second session.

## 3. Wait for completion — bounded, not indefinite

Unlike `open-gui` alone, you own completion detection here. Poll the state directory every ~5s, for up to 10 minutes in one pass (a single Bash call's own ceiling — this is also why it's 10 minutes, not an arbitrary round number). Each tick, check two files, not just one — `session.json`'s `ended` field can appear on its own, independent of `TREE.json`, whenever the browser-side "Stop" button is clicked directly instead of "收斂": that button closes the backend immediately without ever touching `TREE.json`, so a poll that only watches `TREE.json` can't tell "stopped before finalizing" apart from "still genuinely working" and just burns to the full timeout either way.

- **`TREE.json`'s top-level `status` is `complete`**: proceed to step 4's normal path — the backend is still alive (finalizing doesn't shut it down on its own), so send it `SIGTERM` yourself.
- **`session.json` has an `ended` field, and `TREE.json` never reached `complete`**: the backend already exited on its own — browser "Stop", the wrapped `claude` process ending unexpectedly, or the idle-shutdown timeout (`ended.reason` says which). Skip `SIGTERM` (nothing left to signal) and go straight to step 4's reporting — read back whatever exists in `TREE.json`/`docs/grill/<slug>.md` as partial results, and say plainly that the session was stopped before finalizing rather than presenting it as a normal completion.
- **Neither**: still genuinely in progress — keep polling.
- **Timeout reached, neither condition hit**: don't keep waiting silently. Tell the user the interview is still running, give them the session URL again, and stop — they can ask you to check again later, which re-enters this step against the same state directory rather than starting a new session.
- **User asks to cancel, at any point**: skip straight to step 4, send `SIGTERM` if the backend is still alive (check `session.json` for `ended` first — it may already be gone), without waiting for `complete`.

## 4. Stop and report

If the backend is still alive (see step 3), read `session.json` in the state directory for the `pid` and send it `SIGTERM` — this is what actually closes the session; `open-gui` itself never does, by design. If step 3 already found an `ended` marker, the process is gone — nothing to send.

**Then read the outcome back into this session, not just its file paths.** The whole point of running the interview in a browser instead of here is that the decision still has to land back in *this* conversation — a list of file paths makes the user go re-open them to find out what was actually decided, which defeats that. Read `TREE.json` (every node's `resolution`), `docs/grill/<slug>.md`, and any `CONTEXT.md`/ADR entries it wrote, then report the actual decisions — what was resolved and why — directly in your reply. File paths are supporting references after that summary, not a replacement for it. If the session was stopped before finalizing (the second bullet above), report it that way explicitly — whatever was resolved so far, plus which branches were left open — instead of implying the interview ran to completion.
