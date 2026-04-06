# Light Claude/Codex Agent System Restructure Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Restructure the repo into a lighter shared/claude/codex layout and add first-class Codex installation support for AGENTS, subagents, optional rules, and optional hooks.

**Architecture:** Keep the user-root install surface thin. Shared principles live in `shared/`, Claude-specific assets live in `claude/`, and Codex-specific assets live in `codex/`. The installer links deterministic assets directly and merges settings/config only where the official product requires structured config.

**Tech Stack:** Bash, markdown, TOML, JSON, repository-local shell tests

---

### Task 1: Define the new layout

**Files:**
- Create: `shared/*.md`
- Create: `claude/README.md`
- Create: `codex/README.md`
- Modify: `README.md`

**Step 1: Make shared guidance explicit**

Add a `shared/` directory for cross-product principles such as communication, architecture, and quality.

**Step 2: Separate product-specific assets**

Add:
- `claude/` for Claude-facing composition notes
- `codex/` for Codex-facing assets such as subagents, rules, and hooks

**Step 3: Reframe the repo docs**

Explain which assets are shared, which are Claude-specific, which are Codex-specific, and which surfaces are intentionally optional.

### Task 2: Write failing tests for Codex asset installation

**Files:**
- Modify: `tests/install.sh`

**Step 1: Add the failing Codex subagent test**

Expect the installer to place repo-managed `codex/agents/*.toml` into `~/.codex/agents/*.toml`.

**Step 2: Add the failing Codex rules test**

Expect the installer to place repo-managed `codex/rules/*.rules` into `~/.codex/rules/*.rules`.

**Step 3: Add the failing Codex hooks/config test**

Expect:
- repo-managed `codex/hooks.json` to be installed into `~/.codex/hooks.json`
- repo-managed config fragment to be merged into `~/.codex/config.toml`

**Step 4: Verify the tests fail**

Run: `bash tests/install.sh`
Expected: FAIL because the current installer does not install these Codex assets yet.

### Task 3: Implement Codex asset support

**Files:**
- Create: `codex/agents/*.toml`
- Create: `codex/rules/default.rules`
- Create: `codex/hooks.json`
- Create: `config/codex-config.toml`
- Modify: `scripts/install.sh`

**Step 1: Add a small set of Codex subagents**

Start with a tiny set of focused agents rather than mirroring every Claude agent.

**Step 2: Keep Codex rules minimal**

Ship a conservative `default.rules` that does not silently broaden machine authority.

**Step 3: Treat Codex hooks as optional infrastructure**

Install `hooks.json` and merge the required config flag so the user has a consistent on-disk setup without hand-editing config.

**Step 4: Extend the installer**

Support:
- `~/.codex/agents/*.toml`
- `~/.codex/rules/*.rules`
- `~/.codex/hooks.json`
- merge into `~/.codex/config.toml`

### Task 4: Thin the root prompt surfaces

**Files:**
- Modify: `CLAUDE.md`
- Modify: `AGENTS.md`
- Create: `shared/*.md`

**Step 1: Move stable principles into shared docs**

Extract shared guidance into reusable markdown fragments.

**Step 2: Keep Claude root thin**

Use Claude imports where appropriate so `CLAUDE.md` stays focused on routing and Claude-only behavior.

**Step 3: Keep Codex root thin**

Retain only the guidance that belongs in `AGENTS.md`; move approval policy and automation concerns into Codex rules/hooks instead of prose.

### Task 5: Verify and finish

**Files:**
- Verify only

**Step 1: Run install tests**

Run: `bash tests/install.sh`
Expected: PASS

**Step 2: Run hook tests**

Run: `bash tests/hooks.sh`
Expected: PASS

**Step 3: Run a fake-home smoke install**

Run: `bash scripts/install.sh --home /tmp/weihung-user-claude-smoke`
Expected: Claude and Codex assets install into the fake home without touching the real machine.

**Step 4: Inspect the diff**

Run: `git status --short && git diff --stat`
Expected: Only the planned restructuring files changed.
