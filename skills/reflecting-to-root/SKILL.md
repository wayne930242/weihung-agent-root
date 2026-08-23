---
name: reflecting-to-root
description: Use when the user asks to turn session learnings into durable rules.
---

# Reflecting To Root

Reflection is proposal-first. It does not modify agent instructions until the
user approves what should become durable.

## 1. Extract

Identify concrete successes, failures, discoveries, and user corrections. For
each, state the repeatable learning and the evidence that it is not a one-off.

## 2. Classify

- **User root:** true across projects and tools.
- **Project:** specific to one codebase, domain, stack, or team convention.
- **No rule:** already covered, too situational, or cheaper to rediscover from
  code/configuration.

Choose the native surface: prose instruction, rule, hook, agent, skill, or project
documentation. Update an existing source of truth before proposing a new one.

## 3. Confirm

Present the proposed learning, destination, and exact behavioral change. Wait for
the user to accept, revise, or reject each durable change.

## 4. Integrate

Apply only approved changes, keep them concise, and verify the affected agent
configuration. Report approved changes and rejected or already-covered learnings
separately.
