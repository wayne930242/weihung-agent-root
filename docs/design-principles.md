# Design Principles

This repo is a personal user-root light agent system, not a universal agent platform.

That distinction matters. Public toolkits such as Everything Claude Code (ECC) are designed to ship a large surface area across multiple harnesses. This repo is intentionally narrower: it should provide stable global defaults for Claude Code and Codex, while leaving machine-local and project-local concerns under direct user control.

## Core Boundary

Keep the user-root layer thin.

The repo should manage only behavior that is both:

- stable across many projects
- worth versioning globally

Everything else should stay closer to the project or the local machine.

## Workflow Boundary

Use the lightest process that preserves intent and proof.

- Keep a mechanical, self-contained change inline and execute it without a
  persistent artifact.
- Invoke a skill only when its specialized behavior changes the outcome.
- Shape every source-changing task through Requirements, Spec, Design, Implement,
  and Verify after entering the target project, regardless of dispatch.
- Persist separate `requirements.md`, `spec.md`, `design.md`, and
  `verification.md` files when discovery, behavior, or proof must survive a
  session or agent handoff.
- Keep each artifact small enough to understand in one pass and link to existing
  sources instead of copying them.
- Every programming change uses TDD. The agent owns correctness and exercises the
  closest practical interface itself: tests, CLI, API, runtime, Chrome/browser
  automation, computer use, or another project-native surface.
- Human review owns appropriateness: whether an objectively working UX, workflow,
  or domain result is suitable for its users and context. Keep that verdict
  distinct from correctness evidence.
- Do not stack planning frameworks with overlapping jobs.

`leveraging-tasks` owns phase transitions. Native model planning owns execution
tasks; dispatch tools own routing and operational state.

## What Belongs Here

- short shared working agreements
- thin Claude and Codex root prompt files
- a small number of high-value agents or subagents
- minimal hooks for logging or deterministic validation
- installer logic for safe symlink, merge, backup, and restore flows

## What Does Not Belong Here

- full machine ownership of `~/.claude/settings.json`
- full machine ownership of `~/.codex/config.toml`
- large prompt catalogs, command shims, or generated prompt packs
- wide MCP bundles enabled by default
- project-specific workflows, naming, or stack assumptions
- complex automation that turns hooks into a workflow engine

## ECC Lessons

Everything Claude Code is useful as a reference, but only in parts.

### Adopt

- backup-first install behavior
- add-only merge behavior
- selective install thinking
- project-local native config where possible
- sample subagents as examples, not as a large mandatory catalog

### Avoid

- one script taking responsibility for every surface
- syncing a large runtime into user root
- forcing multiple tools into one identical abstraction layer
- growing the global layer into a full platform with commands, prompts, MCP, and workflow logic bundled together

## Product-Specific Rules

Claude and Codex should use their own native surfaces.

### Claude

Use:

- `CLAUDE.md`
- `~/.claude/settings.json`
- Markdown agents

Do not force Claude approval policy or hook behavior into prompt prose when an official settings surface exists.

### Codex

Use:

- `AGENTS.md`
- `rules/*.rules`
- `hooks.json`
- `agents/*.toml`

Do not treat `AGENTS.md` as the place for every policy and automation concern. Keep prose, rules, hooks, and subagent definitions separate.

## Installer Rules

The installer should stay boring and auditable.

- Prefer symlink over copy for managed files.
- Prefer merge over overwrite when touching user-owned config.
- Default to fail-fast on conflicts.
- Require explicit force before replacement.
- Always create backups before destructive replacement.
- Keep install and uninstall behavior symmetrical.

## Maintenance Rule

When deciding whether to add a new file or automation step, use this test:

1. Is it global, not project-specific?
2. Is it stable enough to reuse across many repos?
3. Does it map cleanly to an official Claude or Codex surface?
4. Can it be installed and uninstalled safely?

If any answer is no, it probably does not belong in this repo.
