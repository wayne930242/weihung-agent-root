#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
HOOKS_CONFIG="$REPO_ROOT/config/claude-hooks.json"
CLAUDE_AGENTS_DIR="$REPO_ROOT/claude/agents"
CLAUDE_HOOKS_DIR="$REPO_ROOT/claude/hooks"
CODEX_AGENTS_DIR="$REPO_ROOT/codex/agents"
CODEX_RULES_DIR="$REPO_ROOT/codex/rules"
CODEX_HOOKS_DIR="$REPO_ROOT/codex/hooks"
SHARED_DIR="$REPO_ROOT/shared"

TARGET_HOME="${HOME}"
BACKUP_BASE="${TARGET_HOME}/.local/state/weihung-user-claude/backups"

usage() {
  cat <<'EOF'
Usage: bash scripts/uninstall.sh [--home PATH]

Uninstall flow:
  - restore managed files from the latest backup directory when a backup exists
  - otherwise remove repo-managed symlinks
  - remove repo-managed Claude hook entries from ~/.claude/settings.json

This script does not modify ~/.codex/config.toml.
EOF
}

log() {
  printf '%s\n' "$*"
}

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

latest_backup_dir() {
  if [[ ! -d "$BACKUP_BASE" ]]; then
    return
  fi

  find "$BACKUP_BASE" -mindepth 1 -maxdepth 1 -type d | sort | tail -n 1
}

LATEST_BACKUP_DIR=""

restore_or_remove() {
  local dest="$1"
  local rel_dest="${dest#"$TARGET_HOME"/}"
  local backup_path=""

  if [[ -n "$LATEST_BACKUP_DIR" && -e "$LATEST_BACKUP_DIR/$rel_dest" ]]; then
    backup_path="$LATEST_BACKUP_DIR/$rel_dest"
  fi

  if [[ -n "$backup_path" ]]; then
    if [[ -L "$dest" ]]; then
      rm "$dest"
    elif [[ -e "$dest" ]]; then
      fail "refusing to overwrite non-symlink at $dest while restoring backup"
    fi

    mkdir -p "$(dirname "$dest")"
    cp -a "$backup_path" "$dest"
    log "Restored $dest from $backup_path"
    return
  fi

  if [[ -L "$dest" ]]; then
    rm "$dest"
    log "Removed $dest"
  fi
}

cleanup_empty_dirs() {
  local dirs=(
    "$TARGET_HOME/.claude/agents"
    "$TARGET_HOME/.claude/hooks"
    "$TARGET_HOME/.claude/shared"
    "$TARGET_HOME/.codex/agents"
    "$TARGET_HOME/.codex/rules"
    "$TARGET_HOME/.codex/hooks"
  )

  for dir in "${dirs[@]}"; do
    rmdir "$dir" 2>/dev/null || true
  done
}

clean_claude_settings() {
  local settings_path="$1"

  if [[ ! -f "$settings_path" ]]; then
    return
  fi

  python3 - "$settings_path" "$HOOKS_CONFIG" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
fragment_path = Path(sys.argv[2])

settings = json.loads(settings_path.read_text(encoding="utf-8"))
fragment = json.loads(fragment_path.read_text(encoding="utf-8"))

fragment_hooks = fragment.get("hooks", {})
current_hooks = settings.get("hooks")
if isinstance(current_hooks, dict):
    for event_name, fragment_entries in fragment_hooks.items():
        current_entries = current_hooks.get(event_name)
        if not isinstance(current_entries, list):
            continue

        fragment_serialized = {json.dumps(entry, sort_keys=True) for entry in fragment_entries}
        filtered_entries = [
            entry for entry in current_entries
            if json.dumps(entry, sort_keys=True) not in fragment_serialized
        ]

        if filtered_entries:
            current_hooks[event_name] = filtered_entries
        else:
            current_hooks.pop(event_name, None)

    if not current_hooks:
        settings.pop("hooks", None)

fragment_status = fragment.get("statusLine")
if fragment_status is not None and settings.get("statusLine") == fragment_status:
    settings.pop("statusLine", None)

if settings:
    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
else:
    settings_path.unlink()
PY

  log "Cleaned managed Claude hooks from $settings_path"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --home)
      [[ $# -ge 2 ]] || fail "--home requires a path"
      TARGET_HOME="$2"
      BACKUP_BASE="${TARGET_HOME}/.local/state/weihung-user-claude/backups"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      fail "unknown argument: $1"
      ;;
  esac
done

LATEST_BACKUP_DIR="$(latest_backup_dir || true)"
if [[ -n "$LATEST_BACKUP_DIR" ]]; then
  log "Using latest backup directory: $LATEST_BACKUP_DIR"
fi

restore_or_remove "$TARGET_HOME/.claude/CLAUDE.md"
restore_or_remove "$TARGET_HOME/.claude/statusline.sh"
restore_or_remove "$TARGET_HOME/.codex/AGENTS.md"
restore_or_remove "$TARGET_HOME/.codex/hooks.json"

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.claude/agents/$(basename "$file")"
done < <(find "$CLAUDE_AGENTS_DIR" -maxdepth 1 -type f -name '*.md' | sort)

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.claude/hooks/$(basename "$file")"
done < <(find "$CLAUDE_HOOKS_DIR" -maxdepth 1 -type f -name '*.sh' | sort)

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.claude/shared/$(basename "$file")"
done < <(find "$SHARED_DIR" -maxdepth 1 -type f -name '*.md' | sort)

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.codex/agents/$(basename "$file")"
done < <(find "$CODEX_AGENTS_DIR" -maxdepth 1 -type f -name '*.toml' | sort)

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.codex/rules/$(basename "$file")"
done < <(find "$CODEX_RULES_DIR" -maxdepth 1 -type f -name '*.rules' | sort)

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.codex/hooks/$(basename "$file")"
done < <(find "$CODEX_HOOKS_DIR" -maxdepth 1 -type f -name '*.sh' | sort)

clean_claude_settings "$TARGET_HOME/.claude/settings.json"
cleanup_empty_dirs

log "Uninstall complete."
