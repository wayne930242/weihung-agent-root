---
name: prototype
description: Use to answer a design question with throwaway code.
---

# Prototype

Produce disposable evidence within the Design phase of `leveraging-tasks`. A
direct prototype request enters that lifecycle before source is changed.

## 1. Frame

Write one question the prototype must answer, the observation that will settle
it, and who owns the verdict. Choose a prototype only when running an experiment
is cheaper or clearer than deciding from existing evidence.

When the experiment can prove correctness, the agent exercises its real
interface. When the remaining verdict is whether the result is suitable, use
the parent task's human reality anchor to agree on the reviewer and checkpoint.

**Complete when:** one falsifiable question and its oracle are explicit.

## 2. Build the smallest experiment

- Follow the project's native runtime and place the artifact near its subject.
- Mark it visibly as a prototype and state its disposal plan.
- Keep state ephemeral unless persistence is the question being tested.
- Expose the relevant state and make the experiment trivial to run.
- Implement only what is required to observe the answer; production hardening,
  abstractions, and unrelated polish wait for the real implementation.

**Complete when:** the target reviewer or executable check can exercise the
question without interpreting hidden state.

## 3. Capture the verdict

Record the question, environment, evidence, verdict, and resulting decision in
`design.md`. Remove the prototype after it has served its purpose unless the user
or project convention explicitly preserves it; never commit or publish it without
the active delivery workflow's authorization.

---

Adapted from [mattpocock/skills](https://github.com/mattpocock/skills)
`prototype` (MIT License, Copyright (c) 2026 Matt Pocock).
