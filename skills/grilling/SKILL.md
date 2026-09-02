---
name: grilling
description: Use to resolve user-owned decisions through a design-tree interview.
---

Interview the user relentlessly until you reach a shared understanding. Map the subject as a **design tree**: every decision branches into the decisions that depend on it.

Work in **rounds**. The **frontier** is every open decision whose prerequisites are settled. Ask the whole frontier in one round, numbering each question and giving your recommended answer. Then wait for the user's answers before continuing.

Format each question like this:

```
❓ **Q1 — <title>**: <question and options>

➡️ <recommended answer and why>
```

Each answer reshapes the tree. Recompute the frontier before the next round. A question that still depends on another open decision belongs to a later round.

Finding facts is the agent's job. Use the environment and available tools; delegate independent fact-finding only when it materially saves time. The decisions are the user's: put each frontier question to them and wait.

The session is complete when the frontier is empty and every branch has been visited. Act on the result only after the user confirms shared understanding. Return the confirmed answers and decisions to the caller; update its caller-provided decision artifact before returning.

---

Ported from [mattpocock/skills](https://github.com/mattpocock/skills) (MIT License, Copyright (c) 2026 Matt Pocock).
