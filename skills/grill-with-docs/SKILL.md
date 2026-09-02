---
name: grill-with-docs
description: Use when durable decision exploration should preserve its questions, answers, domain terms, or ADRs.
---

# Grill With Docs

Receive the caller's decision artifact and map the subject as a design tree.
Before interviewing, write every consequential question, the answer already
supported by the request or source facts, its basis, and its status. Resolve
facts through the applicable project sources.

When the document has no open consequential decision, return it directly.
Invoke `grilling` only for the open user-owned frontier, then record each answer
as `confirmed`. Recompute dependent questions and repeat until the document has
no open consequential decision.

When terminology or a durable architectural decision emerges, invoke
`domain-modeling` to challenge and record it at that point. Return the completed
decision artifact to the caller so its existing workflow continues.

---

Ported and adapted from [mattpocock/skills](https://github.com/mattpocock/skills)
`grill-with-docs` (MIT License, Copyright (c) 2026 Matt Pocock).
