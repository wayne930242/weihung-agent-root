---
name: providing-knowledge
description: Use when explaining concepts, comparing technical alternatives, summarizing results or a change for the user, or when the user says they do not follow (看不懂, show me, 講清楚一點).
---

# Providing Knowledge

Lead with the mechanism the user needs; keep prose brief and make uncertainty explicit.

Show the shape beside the sentence it supports, using the smallest view that makes the point, usually one or two. The user does not read code diffs.

```text
submitForm            call tree        src/
  createSession                        ├── sessions/   # owns session state
+   expandSkill       + added          └── transport/  # sends API requests
  navigateToSession   − removed
```

Use pseudocode for logic, `A → B: message` lines for interaction, and a table for options against criteria.

When the answer has several parts, compares options, or needs the user's confirmation, write one HTML page at `/tmp/<task>-<topic>.html` and open it with `show_doc`; the chat then gives the conclusion in a line or two. The page renders in Chawan, about 80 columns wide: no JavaScript, images, or remote files, so draw diagrams in `<pre>`; tables of up to four columns with `th { white-space: nowrap }`. Put the conclusion first. The page is for reading: ask the open questions with `ask_user_question` after opening it, each with your recommendation, never as a form on the page.

Adapted from HumanLayer's [show-me](https://github.com/humanlayer/skills/tree/main/plugins/show-me) (MIT, © 2026 HumanLayer).
