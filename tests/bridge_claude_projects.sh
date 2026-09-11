#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
BRIDGE_SCRIPT="$REPO_ROOT/scripts/bridge-claude-projects.sh"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

assert_symlink_target() {
  local link="$1"
  local expected_target="$2"

  [[ -L "$link" ]] || fail "expected symlink at $link"
  local actual_target
  actual_target="$(readlink "$link")"
  [[ "$actual_target" == "$expected_target" ]] || fail "expected $link -> $expected_target, got $actual_target"
}

test_bridge_single_project() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local proj="$temp_dir/my-project"
  mkdir -p "$proj/.claude/skills/demo-skill"
  printf '# Project Claude Guide\n' > "$proj/CLAUDE.md"
  printf -- '---\nname: demo-skill\ndescription: demo\n---\n# Demo\n' > "$proj/.claude/skills/demo-skill/SKILL.md"

  bash "$BRIDGE_SCRIPT" "$proj"

  assert_symlink_target "$proj/AGENTS.md" "CLAUDE.md"
  assert_symlink_target "$proj/.agents/skills" "../.claude/skills"
  [[ -f "$proj/.agents/skills/demo-skill/SKILL.md" ]] || fail "expected demo-skill to be accessible via .agents/skills"

  # Idempotency check: running again succeeds without modifying targets
  bash "$BRIDGE_SCRIPT" "$proj"
  assert_symlink_target "$proj/AGENTS.md" "CLAUDE.md"
  assert_symlink_target "$proj/.agents/skills" "../.claude/skills"

  rm -rf "$temp_dir"
}

test_bridge_dry_run() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local proj="$temp_dir/dry-project"
  mkdir -p "$proj/.claude/skills/demo-skill"
  printf '# Project Claude Guide\n' > "$proj/CLAUDE.md"

  bash "$BRIDGE_SCRIPT" --dry-run "$proj"

  [[ ! -e "$proj/AGENTS.md" && ! -L "$proj/AGENTS.md" ]] || fail "expected AGENTS.md not created in dry-run"
  [[ ! -d "$proj/.agents" ]] || fail "expected .agents not created in dry-run"

  rm -rf "$temp_dir"
}

test_bridge_parent_dir_scan() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local parent="$temp_dir/all-projects"
  local proj1="$parent/proj-one"
  local proj2="$parent/proj-two"
  mkdir -p "$proj1/.claude/skills/s1" "$proj2"
  printf '# Guide 1\n' > "$proj1/CLAUDE.md"
  printf '# Guide 2\n' > "$proj2/CLAUDE.md"

  bash "$BRIDGE_SCRIPT" "$parent"

  assert_symlink_target "$proj1/AGENTS.md" "CLAUDE.md"
  assert_symlink_target "$proj1/.agents/skills" "../.claude/skills"
  assert_symlink_target "$proj2/AGENTS.md" "CLAUDE.md"
  [[ ! -e "$proj2/.agents/skills" ]] || fail "did not expect .agents/skills when proj2 has no .claude/skills"

  rm -rf "$temp_dir"
}

test_bridge_preserves_conflicting_file_without_force() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local proj="$temp_dir/conflict-project"
  mkdir -p "$proj/.claude/skills"
  printf '# Claude Guide\n' > "$proj/CLAUDE.md"
  printf '# Custom Existing AGENTS\n' > "$proj/AGENTS.md"

  bash "$BRIDGE_SCRIPT" "$proj"

  [[ ! -L "$proj/AGENTS.md" ]] || fail "expected existing AGENTS.md not to be replaced without --force"
  [[ "$(cat "$proj/AGENTS.md")" == "# Custom Existing AGENTS" ]] || fail "expected original content preserved"

  bash "$BRIDGE_SCRIPT" --force "$proj"
  assert_symlink_target "$proj/AGENTS.md" "CLAUDE.md"
  [[ -f "$proj/AGENTS.md.bak" ]] || fail "expected backup AGENTS.md.bak to be created"
  [[ "$(cat "$proj/AGENTS.md.bak")" == "# Custom Existing AGENTS" ]] || fail "expected backup content to match"

  rm -rf "$temp_dir"
}

run_all_tests() {
  test_bridge_single_project
  test_bridge_dry_run
  test_bridge_parent_dir_scan
  test_bridge_preserves_conflicting_file_without_force
  echo "All bridge tests passed."
}

run_all_tests
