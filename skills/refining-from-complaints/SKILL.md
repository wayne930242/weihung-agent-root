---
name: refining-from-complaints
description: Diagnose the root cause behind a complaint about existing, working code or design — an unreasonable decision or a best-practice violation — and get it confirmed before changing anything. Use when the user expresses dissatisfaction with something that already works: a bad design, an awkward API, sloppy implementation, code that "feels off". Not for a crash or error (debug pipe), a request for something new (implement pipe), or venting with no named target (clarify intent first).
---

# Refining From Complaints

## Routing

**Pattern:** owner-pipe
**Handoff:** `leveraging-tasks` (large-scale confirmed fix), `grilling` (multiple viable fixes with real trade-offs)
**Next:** —
**Chain:** main

Turn a complaint into a confirmed root-cause fix. Never patch the literal words of the complaint — patch what's actually wrong.

## Step 1: Capture the Complaint

Restate the complaint in one sentence, from the user's perspective. Do not propose a fix yet.

Check three ways this could be the wrong moment to run Step 2:

- **Reproducible error or crash** → hand off to `leveraging-tasks` (its debug pipe).
- **Wants something that doesn't exist yet** → hand off to `leveraging-tasks` (its implement pipe).
- **No identifiable target** — frustration with no specific file, function, behavior, or design named. This may be venting, not a request. Ask directly: look into it, or just venting? Proceed to Step 2 only on a clear yes.

Continue to Step 2 only when none of the above applies.

## Step 2: Root-Cause Analysis

Read the implicated code — codebase-memory-mcp graph tools first (`search_graph`/`trace_path`/`get_code_snippet`), fall back to Read/Grep. Identify, separately:

1. **The unreasonable design decision** behind the complaint — check against the Refactoring Triggers in `~/.claude/rules/clean-architecture.md` plus any project-specific smell.
2. **The concrete best-practice violation** — name the convention, doc, or pattern it diverges from. Must be traceable ("this violates X because Y"), not an opinion.

A complaint with neither behind it is a preference, not a refinement target — say so instead of inventing a root cause.

## Step 3: Propose

State it as one chain, explicitly linked: complaint → root cause → proposed fix.

- One clearly-better fix → present it with the rationale.
- Multiple viable fixes with real trade-offs → do not pick silently. Run a `grilling`-style pass: one question at a time, your recommendation attached, until the user decides.

## Step 4: Confirm

Do not touch code before this. Wait for explicit confirmation.

If the user disputes the root cause, that is new input, not a rejection — return to Step 2 with it folded in. Do not proceed until you and the user agree on both the root cause and the fix.

## Step 5: Scale Gate

Classify the confirmed fix with the same quality-awareness judgment `leveraging-tasks` Step 2 already uses — do not invent a new threshold.

- **Small/medium** → apply now, in this conversation. Self-review the diff before reporting done.
- **Large (architecture-level change)** → do not implement inline. Hand off to `leveraging-tasks`; it classifies into implement/design/deploy and manages tasks from there.

## Completion

- Venting path: user confirmed "just venting" — no further action, no fix implied.
- Small/medium path: diff applied, self-reviewed, tests green if any exist. Report the chain — complaint → root cause → fix — in one line.
- Large path: handoff to `leveraging-tasks` issued. This skill's job ends at the handoff, not at the eventual implementation.

## Red Flags - STOP

- "The complaint is clear, I'll just change what they pointed at" — skips Step 2, produces a surface patch. Refusing that shortcut is this skill's entire point.
- "This fix is obviously right, no need to wait" — skips Step 4. Confirm regardless of how obvious the fix looks.
- "It's only a few files, I'll just do it now" without running the Step 5 heuristic — skips the scale gate.
- "There's an error message here" — wrong skill; hand off to `leveraging-tasks` instead of forcing a design narrative onto a bug.
- "One option is clearly better, I'll just pick it" when the trade-offs are real — skips the user's decision; run the grilling-style pass instead.
- "They sound frustrated, let's dig in" with no named target — skips the venting check; ask first, don't assume a request.
