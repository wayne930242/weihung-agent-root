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

Present the proposed learning, destination, and exact behavioral change. State
that approval of a user-root change also covers its commit, push, and install in
step 4. Wait for the user to accept, revise, or reject each durable change.

## 4. Integrate

Apply only approved changes, keep them concise, and report approved changes and
rejected or already-covered learnings separately.

Edit user-root changes in the source repository `~/projects/weihung-agent-root`:
`pi/AGENTS.md.in` (generates `~/.pi/agent/AGENTS.md`), `rules/`, and `skills/`;
the installed copies are generated output. Stage the changed files by name, commit
with a Conventional Commit message, push, run `bash scripts/install.sh`, and
verify that the installed file shows the change.
