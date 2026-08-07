---
name: grill-with-web
description: Use when the user wants a grilling interview to run in the browser instead of the terminal — "grill this in the browser", "web version of grilling", "grill with a live decision tree". The GUI counterpart of grill-with-docs, for the same refactoring/architecture-improvement triggers, when the user specifically wants the browser experience.
---

# Grill With Web

The GUI version of `grill-with-docs`. You build the seed prompt and manage the session's lifecycle; `open-gui` does everything session/browser/tree-rendering. Read `skills/open-gui/SKILL.md` first if you haven't invoked it before — this skill is a thin layer on top of its contract, not a reimplementation.

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
paths, and (embedded directly, not referenced by path):

- Populate `TREE.json` **at the literal absolute path you computed** (see `open-gui/SKILL.md`'s "For other skills invoking open-gui" — the target session cannot discover this path itself). State the exact top-level shape: `{"status": "in_progress" | "complete", "nodes": [...]}` — spell out both literal strings (underscore, not hyphen). A condensed re-explanation of `NODE-FORMAT.md` that only covers per-node `status` enums and drops the top-level one is an easy, real gap to leave by accident — say it explicitly, don't assume it's implied.
- The interview discipline from `grill-with-docs/SKILL.md`: challenge glossary conflicts, sharpen fuzzy language, discuss concrete scenarios, cross-reference against the code, record resolved terms in `CONTEXT.md` inline (per `CONTEXT-FORMAT.md`'s shape) the moment they crystallise, and offer an ADR (per `ADR-FORMAT.md`'s shape, `docs/adr/NNNN-slug.md`) only when a decision is hard to reverse, surprising without context, AND the result of a real trade-off.
- The `TREE.json` node shape from `NODE-FORMAT.md`: a `decision` node per grilling branch (`recommendation` while open, `resolution` once resolved, `doc` set to the ADR's path whenever one is produced). Don't mention `question` nodes — `AskUserQuestion` calls render live in the browser and are answered directly (design.md D11); nothing needs to be written to `TREE.json` for them, and no seed-prompt instruction is needed to make that happen.
- **Before finalizing** (once every branch looks resolved): call `AskUserQuestion` directly — e.g. "Ready to finalize and write the summary doc?" with options to proceed or keep discussing — and wait for the answer like any other question. This is the user's explicit confirmation to wrap up.
- At completion: write `docs/grill/<slug>.md` — a Mermaid diagram generated from `TREE.json` plus a narrative summary — and set `TREE.json`'s top-level `status` to `complete`.

## 2. Start the session

Invoke `open-gui` with this seed prompt and topic, cwd = the current project. Record the state directory it reports back — you need it for the next two steps, and if this conversation is later resumed, re-derive it the same way (`~/.claude/state/<project-slug>/open-gui/<session-id>/`) rather than starting a second session.

## 3. Wait for completion — bounded, not indefinite

Unlike `open-gui` alone, you own completion detection here. Poll the state directory's `TREE.json` top-level `status` for `complete`, checking every ~5s, for up to 10 minutes in one pass (a single Bash call's own ceiling — this is also why it's 10 minutes, not an arbitrary round number).

- **Reached `complete`**: proceed to step 4.
- **Timeout reached, still `in_progress`**: don't keep waiting silently. Tell the user the interview is still running, give them the session URL again, and stop — they can ask you to check again later, which re-enters this step against the same state directory rather than starting a new session.
- **User asks to cancel, at any point**: skip straight to step 4's shutdown, without waiting for `complete`.

## 4. Stop and report

Read `session.json` in the state directory for the backend's `pid`; send it `SIGTERM` (this is what actually closes the session — `open-gui` itself never does, by design). Then report back to the user: the written document paths (`CONTEXT.md` entries, any ADRs, `docs/grill/<slug>.md`).
