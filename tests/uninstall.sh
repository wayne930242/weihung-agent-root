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

  HOME="$fake_home" bash "$INSTALL_SCRIPT" --home "$fake_home" "$@"
}

run_uninstall() {
  local fake_home="$1"
  shift

  HOME="$fake_home" bash "$UNINSTALL_SCRIPT" --home "$fake_home" "$@"
}

restore_from_backup_and_clean_hooks() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude" "$fake_home/.codex/rules"
  printf 'old claude\n' > "$fake_home/.claude/CLAUDE.md"
  printf 'old codex agents\n' > "$fake_home/.codex/AGENTS.md"
  printf 'old rule\n' > "$fake_home/.codex/rules/default.rules"
  cat > "$fake_home/.claude/settings.json" <<'EOF'
{
  "customSetting": true,
  "model": "sonnet"
}
EOF

  run_install "$fake_home" --force
  run_uninstall "$fake_home"

  [[ "$(cat "$fake_home/.claude/CLAUDE.md")" == "old claude" ]] || fail "expected CLAUDE.md to be restored from backup"
  [[ "$(cat "$fake_home/.codex/AGENTS.md")" == "old codex agents" ]] || fail "expected AGENTS.md to be restored from backup"
  [[ "$(cat "$fake_home/.codex/rules/default.rules")" == "old rule" ]] || fail "expected default.rules to be restored from backup"
  [[ ! -e "$fake_home/.claude/shared/communication.md" ]] || fail "expected managed shared file to be removed"
  [[ ! -e "$fake_home/.codex/agents/docs-researcher.toml" ]] || fail "expected managed codex agent to be removed"
  [[ ! -e "$fake_home/.codex/hooks.json" ]] || fail "expected managed codex hooks.json to be removed"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert settings["customSetting"] is True, settings
assert settings["model"] == "sonnet", settings
assert "hooks" not in settings, settings
PY

  rm -rf "$temp_dir"
}

fresh_install_uninstall_removes_managed_files() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home"

  run_install "$fake_home"
  run_uninstall "$fake_home"

  [[ ! -e "$fake_home/.claude/CLAUDE.md" ]] || fail "expected CLAUDE.md to be removed when no backup exists"
  [[ ! -e "$fake_home/.codex/AGENTS.md" ]] || fail "expected AGENTS.md to be removed when no backup exists"
  [[ ! -e "$fake_home/.codex/rules/default.rules" ]] || fail "expected default.rules to be removed when no backup exists"

  python3 - <<PY
import json
from pathlib import Path
settings_path = Path("$fake_home/.claude/settings.json")
if settings_path.exists():
    settings = json.loads(settings_path.read_text())
    assert "hooks" not in settings, settings
PY

  rm -rf "$temp_dir"
}

latest_backup_directory_wins() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  local backup_base="$fake_home/.local/state/weihung-user-claude/backups"
  mkdir -p "$fake_home/.claude" "$backup_base/20250101-000000/.claude" "$backup_base/20250102-000000/.claude"

  ln -s "$REPO_ROOT/CLAUDE.md" "$fake_home/.claude/CLAUDE.md"
  printf 'older backup\n' > "$backup_base/20250101-000000/.claude/CLAUDE.md"
  printf 'newer backup\n' > "$backup_base/20250102-000000/.claude/CLAUDE.md"

  run_uninstall "$fake_home"

  [[ "$(cat "$fake_home/.claude/CLAUDE.md")" == "newer backup" ]] || fail "expected uninstall to restore from the latest backup directory"

  rm -rf "$temp_dir"
}

run_all_tests() {
  restore_from_backup_and_clean_hooks
  fresh_install_uninstall_removes_managed_files
  latest_backup_directory_wins
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
else
  "$1"
fi
