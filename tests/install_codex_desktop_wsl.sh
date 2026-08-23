#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_SCRIPT="$REPO_ROOT/scripts/install-codex-desktop-wsl.sh"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

assert_same_file() {
  local actual="$1"
  local expected="$2"

  [[ -f "$actual" ]] || fail "expected file at $actual"
  cmp -s "$actual" "$expected" || fail "expected $actual to match $expected"
}

run_install() {
  local windows_home="$1"
  shift

  bash "$INSTALL_SCRIPT" --windows-home "$windows_home" "$@"
}

fresh_install_copies_managed_surface_and_preserves_unrelated_content() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  local windows_home="$temp_dir/Windows User"

  mkdir -p "$windows_home/.codex/skills/.system"
  printf 'keep\n' > "$windows_home/.codex/skills/.system/keep.txt"

  run_install "$windows_home"

  assert_same_file "$windows_home/.codex/AGENTS.md" "$REPO_ROOT/AGENTS.md"
  assert_same_file "$windows_home/.codex/hooks.json" "$REPO_ROOT/codex/hooks.json"
  assert_same_file "$windows_home/.codex/agents/docs-researcher.toml" "$REPO_ROOT/codex/agents/docs-researcher.toml"
  assert_same_file "$windows_home/.codex/rules/default.rules" "$REPO_ROOT/codex/rules/default.rules"
  assert_same_file "$windows_home/.codex/hooks/log-stop.sh" "$REPO_ROOT/codex/hooks/log-stop.sh"
  assert_same_file "$windows_home/.codex/skills/leveraging-tasks/SKILL.md" "$REPO_ROOT/skills/leveraging-tasks/SKILL.md"
  [[ "$(cat "$windows_home/.codex/skills/.system/keep.txt")" == "keep" ]] || fail "expected unrelated .system skill to remain"
  [[ ! -e "$windows_home/.codex/config.toml" ]] || fail "did not expect config.toml to be installed"

  run_install "$windows_home"

  rm -rf "$temp_dir"
}

conflict_requires_force_and_force_creates_backup() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  local windows_home="$temp_dir/Windows User"

  mkdir -p "$windows_home/.codex"
  printf 'existing\n' > "$windows_home/.codex/AGENTS.md"

  if run_install "$windows_home"; then
    fail "expected a conflicting AGENTS.md to fail without --force"
  fi
  [[ "$(cat "$windows_home/.codex/AGENTS.md")" == "existing" ]] || fail "expected failed install to preserve conflict"

  run_install "$windows_home" --force

  assert_same_file "$windows_home/.codex/AGENTS.md" "$REPO_ROOT/AGENTS.md"
  local backup_file
  backup_file="$(find "$windows_home/AppData/Local/weihung-user-claude/backups" -type f -path '*/.codex/AGENTS.md' | head -n 1)"
  [[ -n "$backup_file" ]] || fail "expected backed up AGENTS.md"
  [[ "$(cat "$backup_file")" == "existing" ]] || fail "expected backup to preserve previous content"

  rm -rf "$temp_dir"
}

run_all_tests() {
  fresh_install_copies_managed_surface_and_preserves_unrelated_content
  conflict_requires_force_and_force_creates_backup
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
else
  "$1"
fi
