---
name: providing-knowledge
description: Use when explaining concepts, comparing technical alternatives, summarizing results or a change for the user, or when the user says they do not follow (看不懂, show me, 講清楚一點).
---

# Providing Knowledge

Lead with the mechanism or mental model the user needs. Add only the context,
trade-offs, and edges that change understanding. Make uncertainty explicit and
verify time-sensitive facts before presenting them as current.

Show the shape instead of describing it: a call tree, file tree, table, or
pseudocode beside the sentence it supports, picked from
[references/showing.md](references/showing.md). Describe a code change by its
effect and changed shape; the user does not read diffs.

When the answer has more than one part, compares options, or asks the user to
confirm something, write it as one HTML page as
[references/showing.md](references/showing.md) describes and open it with
`show_doc`; the chat reply then states the conclusion in a line or two. A short
answer stays in chat. End once the question is answered.
