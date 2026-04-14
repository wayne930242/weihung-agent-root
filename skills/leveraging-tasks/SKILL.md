---
name: leveraging-tasks
description: Thin router that classifies tasks and applies quality gates before delegation. Routes to implement, design, debug, or deploy flows with cross-cutting refactor awareness. Use when starting any significant development task.
---

# Leveraging Tasks

## Routing

**Pattern:** owner-pipe
**Handoff:** auto-invoke (internal steps)
**Next:** `reflecting-to-root` (suggested at completion)
**Chain:** main

Classify the task, apply quality gates, delegate to project-level skills or execute directly.

## Step 1: Classify

Determine the primary task type from the user's request:

| Type | Signal |
|------|--------|
| **implement** | "add", "create", "build", "write", "integrate" |
| **design** | "architect", "plan", "design", "how should we", "what's the best approach" |
| **debug** | "fix", "broken", "error", "not working", "investigate", "why" |
| **deploy** | "deploy", "release", "push to prod", "ship" |

If ambiguous, ask one clarifying question. Do not guess.

## Step 2: Quality Awareness (All Pipes)

This is not an entry gate. Maintain this awareness throughout execution:

- File too large? (>300 lines → consider splitting)
- Function doing more than one thing? → split
- Mixed responsibilities in one module? → separate
- Small refactor opportunity? → do it now, don't ask
- Medium refactor (split file, extract module)? → do it, inform user
- Large refactor (architecture change)? → pause, go to design

## Step 3: Execute Pipe

### Implement

**Entry gate:**
1. Read target files and surrounding code. No exceptions.
2. Identify existing patterns. Follow them.
3. Check for circular dependencies in the planned approach.

**During execution:**
- Discovered new context that changes the approach? Pause, switch to **design**.
- Found code smell while editing? Small/medium refactor on the spot.
- Before finishing: self-review. Did you introduce any bad patterns?

**Delegate:** If project has an implementation skill → `REQUIRED SUB-SKILL: [project skill]` (model: sonnet)

### Design

**Entry gate:**
1. Requirements clear? If not, ask. One question at a time.
2. Read existing code in the affected area.
3. Prepare 2-3 approaches with trade-offs.

**During execution:**
- Existing code has smells that the new design would build on? Refactor first.
- Design would worsen existing problems? Adjust or refactor first.
- Output: design decision + list of pre-requisite refactors (if any).

**Delegate:** If project has a design skill → `REQUIRED SUB-SKILL: [project skill]` (model: opus)

### Debug

**Entry gate:**
1. Reproduce the issue. If you cannot reproduce, say so.
2. Read the error message. Fully.
3. Form a hypothesis before changing any code.

**During execution:**
- Root cause is architectural? Switch to **refactor**, not a patch.
- Found related smells while investigating? Small/medium refactor on the spot.
- Before finishing: did the fix introduce new problems?

**Delegate:** If project has a debug skill → `REQUIRED SUB-SKILL: [project skill]` (model: opus)

### Deploy

**Entry gate:** Apply all requirements in `~/.claude/rules/deployment.md`.

Deploy does not trigger refactoring. It consumes quality, does not produce it.

**Delegate:** If project has a deploy skill → `REQUIRED SUB-SKILL: [project skill]` (model: sonnet)

## Step 4: Completion

After the task is done:

1. If significant work was completed → suggest `/reflecting-to-root`
2. Otherwise → done

## Flowchart

```dot
digraph leveraging {
    rankdir=TB;
    node [shape=box];

    classify [label="Classify task type", shape=doublecircle];
    quality [label="Quality awareness\n(continuous)", shape=note, style=filled, fillcolor="#f0f0f0"];

    implement [label="Implement\n1. Read existing code\n2. Follow patterns\n3. Check dependencies"];
    design [label="Design\n1. Clarify requirements\n2. Read affected code\n3. 2-3 approaches"];
    debug [label="Debug\n1. Reproduce\n2. Read error\n3. Hypothesize"];
    deploy [label="Deploy\n1. Run tests\n2. Verify excludes\n3. Dry-run first"];

    new_context [label="New context\ndiscovered?", shape=diamond];
    smell [label="Code smell\nfound?", shape=diamond];
    small_refactor [label="Small/medium:\nrefactor on spot"];
    large_refactor [label="Large:\npause → design"];
    done [label="Done\n+ suggest reflect", shape=doublecircle];

    classify -> implement [label="implement"];
    classify -> design [label="design"];
    classify -> debug [label="debug"];
    classify -> deploy [label="deploy"];

    quality -> implement [style=dotted];
    quality -> design [style=dotted];
    quality -> debug [style=dotted];

    implement -> new_context;
    new_context -> design [label="yes"];
    new_context -> smell;
    smell -> small_refactor [label="small/med"];
    smell -> large_refactor [label="large"];
    small_refactor -> done;
    large_refactor -> design;
    smell -> done [label="none"];

    design -> done;
    debug -> done;
    deploy -> done;
}
```
