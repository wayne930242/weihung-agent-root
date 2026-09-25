#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_SCRIPT="$REPO_ROOT/scripts/install.sh"
UNINSTALL_SCRIPT="$REPO_ROOT/scripts/uninstall.sh"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

run_install() {
  local fake_home="$1"
  shift
  HOME="$fake_home" bash "$INSTALL_SCRIPT" --home "$fake_home" --skip-external "$@" >/dev/null
}

run_uninstall() {
  local fake_home="$1"
  shift
  HOME="$fake_home" bash "$UNINSTALL_SCRIPT" --home "$fake_home" --skip-external "$@" >/dev/null
}

fresh_install_uninstall_removes_managed_files() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  local fake_home="$temp_dir/home"
  local user_skill="$temp_dir/user-skill"
  mkdir -p "$user_skill"

  run_install "$fake_home"
  ln -s "$user_skill" "$fake_home/.agents/skills/user-skill"
  run_uninstall "$fake_home"

  [[ ! -e "$fake_home/.pi/agent/rules" && ! -L "$fake_home/.pi/agent/rules" ]] || fail "expected rules link removed"
  [[ ! -e "$fake_home/.pi/agent/AGENTS.md" ]] || fail "expected generated pi instructions removed"
  [[ ! -e "$fake_home/.pi/agent/.weihung-user-claude.json" ]] || fail "expected install marker removed"
  [[ -z "$(find "$fake_home/.agents/skills" -type l -lname "$REPO_ROOT/*")" ]] || fail "expected repository skill links removed"
  [[ "$(readlink "$fake_home/.agents/skills/user-skill")" == "$user_skill" ]] || fail "expected user skill link kept"

  rm -rf "$temp_dir"
}

uninstall_restores_backed_up_targets() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.pi/agent/rules"
  printf 'mine\n' > "$fake_home/.pi/agent/rules/own.md"

  run_install "$fake_home" --force
  run_uninstall "$fake_home"

  [[ -d "$fake_home/.pi/agent/rules" && ! -L "$fake_home/.pi/agent/rules" ]] || fail "expected user rules directory restored"
  [[ "$(cat "$fake_home/.pi/agent/rules/own.md")" == "mine" ]] || fail "expected restored rule content"

  rm -rf "$temp_dir"
}

uninstall_finds_rules_backup_behind_a_newer_backup() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.pi/agent/rules"
  printf 'mine\n' > "$fake_home/.pi/agent/rules/own.md"

  run_install "$fake_home" --force
  mkdir -p "$fake_home/.local/state/weihung-user-claude/backups/99991231-235959/.pi/agent"
  run_uninstall "$fake_home"

  [[ -d "$fake_home/.pi/agent/rules" && ! -L "$fake_home/.pi/agent/rules" ]] || fail "expected rules restored from an older backup directory"
  [[ "$(cat "$fake_home/.pi/agent/rules/own.md")" == "mine" ]] || fail "expected restored rule content from the older backup"
  rm -rf "$temp_dir"
}

uninstall_keeps_a_foreign_rules_link() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  local fake_home="$temp_dir/home"
  local other="$temp_dir/other-rules"
  mkdir -p "$other"

  run_install "$fake_home"
  rm "$fake_home/.pi/agent/rules"
  ln -s "$other" "$fake_home/.pi/agent/rules"
  run_uninstall "$fake_home"

  [[ "$(readlink "$fake_home/.pi/agent/rules")" == "$other" ]] || fail "expected a rules link owned elsewhere to stay"

  rm -rf "$temp_dir"
}

run_all_tests() {
  fresh_install_uninstall_removes_managed_files
  uninstall_restores_backed_up_targets
  uninstall_finds_rules_backup_behind_a_newer_backup
uninstall_keeps_a_foreign_rules_link
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
  printf 'uninstall: pass\n'
else
  "$1"
fi
