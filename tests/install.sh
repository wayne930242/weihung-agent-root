#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_SCRIPT="$REPO_ROOT/scripts/install.sh"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

assert_symlink_target() {
  local path="$1"
  local expected="$2"

  [[ -L "$path" ]] || fail "expected symlink at $path"
  local actual
  actual="$(readlink "$path")"
  [[ "$actual" == "$expected" ]] || fail "expected $path -> $expected, got $actual"
}

run_install() {
  local fake_home="$1"
  shift

  HOME="$fake_home" bash "$INSTALL_SCRIPT" --home "$fake_home" "$@"
}

fresh_install_creates_expected_symlinks() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home"

  run_install "$fake_home"

  assert_symlink_target "$fake_home/.claude/CLAUDE.md" "$REPO_ROOT/CLAUDE.md"
  assert_symlink_target "$fake_home/.codex/AGENTS.md" "$REPO_ROOT/AGENTS.md"
  assert_symlink_target "$fake_home/.claude/hooks" "$REPO_ROOT/hooks"
  assert_symlink_target "$fake_home/.claude/agents/security-reviewer.md" "$REPO_ROOT/agents/security-reviewer.md"
  assert_symlink_target "$fake_home/.claude/agents/silent-failure-hunter.md" "$REPO_ROOT/agents/silent-failure-hunter.md"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert "hooks" in settings, settings
assert "Stop" in settings["hooks"], settings
assert "Notification" in settings["hooks"], settings
PY

  rm -rf "$temp_dir"
}

conflict_without_force_fails() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude"
  printf 'existing\n' > "$fake_home/.claude/CLAUDE.md"

  if run_install "$fake_home"; then
    fail "expected install to fail when CLAUDE.md already exists without --force"
  fi

  rm -rf "$temp_dir"
}

force_replaces_and_backs_up_conflicts() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude"
  printf 'existing\n' > "$fake_home/.claude/CLAUDE.md"

  run_install "$fake_home" --force

  assert_symlink_target "$fake_home/.claude/CLAUDE.md" "$REPO_ROOT/CLAUDE.md"

  local backup_base="$fake_home/.local/state/weihung-user-claude/backups"
  [[ -d "$backup_base" ]] || fail "expected backup directory at $backup_base"

  local backup_file
  backup_file="$(find "$backup_base" -type f -path '*/.claude/CLAUDE.md' | head -n 1)"
  [[ -n "$backup_file" ]] || fail "expected backed up CLAUDE.md"
  [[ "$(cat "$backup_file")" == "existing" ]] || fail "expected backup to preserve previous content"

  rm -rf "$temp_dir"
}

existing_settings_are_merged_not_replaced() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude"
  cat > "$fake_home/.claude/settings.json" <<'EOF'
{
  "customSetting": true,
  "model": "sonnet"
}
EOF

  run_install "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert settings["customSetting"] is True, settings
assert settings["model"] == "sonnet", settings
assert "Stop" in settings["hooks"], settings
assert "Notification" in settings["hooks"], settings
PY

  rm -rf "$temp_dir"
}

run_all_tests() {
  fresh_install_creates_expected_symlinks
  conflict_without_force_fails
  force_replaces_and_backs_up_conflicts
  existing_settings_are_merged_not_replaced
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
else
  "$1"
fi
