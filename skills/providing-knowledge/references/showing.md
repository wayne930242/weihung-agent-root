# Showing the user

Adapted from HumanLayer's [show-me](https://github.com/humanlayer/skills/tree/main/plugins/show-me) skill (MIT License, Copyright (c) 2026 HumanLayer).

## Views

Pick the smallest view that makes the point; one or two usually suffice. Keep only the calls, files, props, states, and boundaries the current question needs.

- **Pseudocode** for logic or an algorithm.
- **Call tree** for runtime control flow, one call per line, indented by depth.
- **Component tree** for UI structure, with the state hooks and module boundaries that matter and the file of each boundary.
- **Shallow file tree** for where things live or the reach of a refactor, one line of responsibility per entry.
- **Sequence** for interaction between parties: one `A → B: message` per line in a `<pre>`.
- **Types and signatures** for the shape of code before it exists.
- **Table** for options against the criteria that decide between them, or for status per item.
- **Changed shape**: one of the views above with added lines in green marked `+` and removed lines in red marked `−`, keeping the unchanged lines that show ownership and order. Use it instead of a code diff.

## HTML page

`show_doc` opens `.html` in Chawan, a text-mode browser inside a Herdr pane about 80 columns wide. Write for what Chawan renders:

- One self-contained file under `/tmp/<task>-<topic>.html`, outside the repository, with an inline `<style>` and `<meta charset="utf-8">`. Chawan runs no JavaScript and loads nothing remote, and an image or SVG shows as `[img]`; draw diagrams as text in `<pre>`.
- Renders: headings, tables with `border-collapse: collapse` and cell borders, lists, `<pre>`, `<code>`, `<dl>`, `<hr>`, text and background colours, bold, and boxes with a border and padding.
- Side by side: a `display: flex` row of bordered boxes, at most three; `gap` is ignored, so give the boxes padding. Grid stacks vertically, and `<details>` always shows its content.
- Font size and family are ignored; emphasis comes from headings, colour, bold, and boxes. Keep tables to four columns and cells short, and give `th` `white-space: nowrap`, because a narrow column otherwise breaks a two-character header across lines.

Shape of the page:

1. A title and the conclusion in one or two sentences.
2. The views, each under a heading with the short text it supports.
3. When the user must decide, a final box listing each open question with the options and your recommendation, numbered to match the `ask_user` call that follows.

Colours carry one meaning each across the page: green done or recommended, orange pending or caution, red failed or removed.
