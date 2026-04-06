# Claude/Codex Bootstrap Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add a safe bootstrap flow that installs this repo as the source of truth for Claude Code and Codex via symlinks and minimal home-directory integration.

**Architecture:** Keep the repo as the canonical source for prompt files and agent definitions, then install them into `~/.claude` and `~/.codex` with a small shell bootstrap. Preserve existing user state by failing on conflicts by default and backing up replaced files only when `--force` is passed.

**Tech Stack:** Bash, markdown docs, repository-local shell tests

---

### Task 1: Define the install surface

**Files:**
- Create: `AGENTS.md`
- Modify: `README.md`

**Step 1: Specify the Codex-facing system prompt**

Write `AGENTS.md` as the Codex analogue of `CLAUDE.md`, preserving the same operating principles while removing Claude-specific slash commands and tool assumptions.

**Step 2: Document the supported install targets**

Update `README.md` so the supported surface is explicit:
- `~/.claude/CLAUDE.md`
- `~/.claude/agents/*.md`
- `~/.codex/AGENTS.md`

**Step 3: Keep scope intentionally narrow**

Do not auto-write `settings.json`, `config.toml`, secrets, or plugins in v1. The installer should only manage prompt and agent symlinks.

**Step 4: Run a quick content sanity check**

Run: `sed -n '1,220p' AGENTS.md && sed -n '1,260p' README.md`
Expected: The new install surface is documented and Codex instructions do not mention Claude-only commands.

### Task 2: Write failing install tests

**Files:**
- Create: `tests/install.sh`

**Step 1: Write the failing test for fresh install**

Add a shell test that:
- creates a temporary fake `HOME`
- runs `scripts/install.sh`
- asserts the expected symlinks exist and point back to the repo

**Step 2: Verify fresh install test fails**

Run: `bash tests/install.sh fresh_install_creates_expected_symlinks`
Expected: FAIL because `scripts/install.sh` does not exist yet.

**Step 3: Write the failing conflict test**

Add a second test that:
- creates a pre-existing regular file at `~/.claude/CLAUDE.md`
- runs `scripts/install.sh` without `--force`
- expects a non-zero exit

**Step 4: Verify the conflict test fails for the right reason**

Run: `bash tests/install.sh conflict_without_force_fails`
Expected: FAIL because the installer does not exist yet, not because the assertion logic is broken.

### Task 3: Implement the bootstrap script

**Files:**
- Create: `scripts/install.sh`

**Step 1: Implement minimal argument parsing**

Support:
- default install into `$HOME`
- `--home <path>` for testability
- `--force` for safe replacement with backup

**Step 2: Implement symlink installation**

Install these targets:
- `CLAUDE.md` -> `~/.claude/CLAUDE.md`
- `AGENTS.md` -> `~/.codex/AGENTS.md`
- `agents/*.md` -> `~/.claude/agents/*.md`

**Step 3: Implement conflict handling**

Behavior:
- if target already points to the correct source, leave it unchanged
- if target exists and `--force` is not set, exit non-zero
- if target exists and `--force` is set, move it into a timestamped backup directory before linking

**Step 4: Run the install tests**

Run: `bash tests/install.sh`
Expected: PASS

### Task 4: Document usage and safety

**Files:**
- Modify: `README.md`

**Step 1: Add installation instructions**

Document:
- install command
- what gets linked
- what does not get modified

**Step 2: Add safety notes**

Document:
- conflict behavior
- `--force` backup behavior
- recommendation to review diffs before broadening scope to `settings.json` or Codex config merge

**Step 3: Re-read the docs**

Run: `sed -n '1,260p' README.md`
Expected: The installation flow is clear and narrowly scoped.

### Task 5: Verify end-to-end

**Files:**
- Verify only

**Step 1: Run tests**

Run: `bash tests/install.sh`
Expected: PASS

**Step 2: Run installer help or dry sanity**

Run: `bash scripts/install.sh --home /tmp/weihung-user-claude-smoke`
Expected: Script creates only prompt/agent symlinks in the fake home tree.

**Step 3: Inspect the diff**

Run: `git status --short && git diff -- README.md AGENTS.md scripts/install.sh tests/install.sh`
Expected: Only the planned files changed.
