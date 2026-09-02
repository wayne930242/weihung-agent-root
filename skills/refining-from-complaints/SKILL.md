---
name: refining-from-complaints
description: Use when the user complains about working code, design, or documentation that feels wrong.
---

# Refining From Complaints

Turn dissatisfaction with working code, design, or documentation into a
confirmed refinement target. This skill owns diagnosis, not implementation.

## 1. Qualify

Capture the complaint from the user's perspective.

- A crash or reproducible failure belongs to `leveraging-tasks` debugging.
- A request for new behavior belongs to `leveraging-tasks` implementation.
- A complaint with no identifiable target may be venting; ask whether the user
  wants it investigated.

**Complete when:** there is a working code, design, or documentation target the
user wants improved.

## 2. Diagnose

Inspect the implicated experience and identify separately:

- the player's observed experience and the need left unmet
- the friction that turns that experience into negative feedback
- the behavior, design, or documentation decision that creates the complaint
- the documented standard, best practice, or project precedent it violates

Use `investigating` for substantial cross-source research. If the causal
decision and violated standard are unsupported by evidence, classify the
complaint as a preference rather than invent a defect.

Treat justification added to a response or document as a workaround signal: it
manages the perception of the friction while leaving its source intact. Continue
diagnosis until the correction addresses that source and the document can state
the expected behavior directly.

**Complete when:** the chain `negative feedback → player experience → friction →
root cause → positive correction` is evidence-backed.

## 3. Confirm

Propose the smallest root correction that removes the friction. Phrase its target
as observable expected behavior for the player and any document reader. When
wording creates the friction, rewrite it to state that behavior directly; when
behavior or design creates it, correct the source and align the document with the
result.

Use `grilling` when viable alternatives carry a real user-owned trade-off, and
wait for the user there. When the cause and the correction carry no such
trade-off, state both and continue; treat later disagreement as new diagnostic
input.

## 4. Hand off

Return the confirmed chain to `leveraging-tasks` as decision input for the
source-changing fix. It classifies artifact depth itself: a localized correction
runs inline there, and only durable decisions produce artifacts. Handing the
chain over is what keeps it from being re-derived, not a checkpoint the fix has
to clear.

**Complete when:** no change was requested, or `leveraging-tasks` has received a
confirmed refinement target.
