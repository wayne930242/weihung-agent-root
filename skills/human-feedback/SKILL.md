---
name: human-feedback
description: Use when a person reacts to working output — dissatisfaction, a correction, "this feels wrong" — or when verification hands a UI or human-use scenario to a person to operate and report back.
---

# Human Feedback

Turn a person's reaction to working output into an evidence-backed root cause and
a correction made at that root. This skill owns diagnosis, not implementation.

## 1. Enter

Two entries:

- **Detected:** a person reacts to working code, design, or documentation.
  Invoke on the reaction itself, before answering it.
- **Invited:** verification covers UI or a human-use scenario and the user
  accepted a feedback pass. Name the real interface and the flows to operate,
  then collect what the person observed.

Route a crash or reproducible failure to `leveraging-tasks` debugging and a
request for new behavior to its implementation path. A reaction with no
identifiable target may be venting; ask whether the user wants it investigated.

**Complete when:** there is a working code, design, or documentation target the
person wants improved.

## 2. Diagnose

Attend to the problem the person has, ahead of the fix they propose. Identify
separately:

- the person's observed experience and the need left unmet
- the friction that turns that experience into negative feedback
- the behavior, design, or documentation decision that creates the friction
- the documented standard, best practice, or project precedent it violates

Use `investigating` for substantial cross-source research. If the causal decision
and violated standard are unsupported by evidence, classify the reaction as a
preference rather than invent a defect.

Treat justification added to a response or document as a workaround signal: it
manages the perception of the friction while leaving its source intact. Continue
diagnosis until the correction addresses that source and the document can state
the expected behavior directly.

**Complete when:** the chain `feedback → experience → friction → root cause →
positive correction` is evidence-backed.

## 3. Correct at the source

Propose the smallest correction that removes the friction where it originates.
Phrase its target as observable expected behavior for the person and any document
reader. When wording creates the friction, rewrite it to state that behavior
directly; when behavior or design creates it, correct the source and align the
document with the result.

The correction carries the source's own shape:

- It lands on the causal decision, so the same friction cannot return through a
  sibling path.
- It matches the pattern, terminology, and layer that already govern that source.
- A defensive guard belongs where the input is genuinely untrusted or the failure
  is genuinely reachable; a root proven correct carries none.
- A fallback or special case belongs where its branch is a real case of the
  domain; a branch that exists to mask the root belongs in the root instead.

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
confirmed correction target.
