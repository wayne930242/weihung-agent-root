#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"

TARGET_HOME="${HOME}"
BACKUP_BASE="${TARGET_HOME}/.local/state/weihung-user-claude/backups"
SKIP_EXTERNAL=0

usage() {
  cat <<'EOF'
Usage: bash scripts/uninstall.sh [--home PATH] [--skip-external]

Uninstall flow:
  - restore each managed link from the latest backup directory when a backup exists
  - otherwise remove the repository links in ~/.agents/skills and ~/.pi/agent/rules
  - run scripts/pi-target.py uninstall, which removes this repository's pi
    packages and resources and restores the pi settings it changed

The pi binary, its login state, and codebase-memory-mcp stay installed.
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

prune_managed_links() {
  local target_dir="$1"
  [[ -d "$target_dir" ]] || return 0

  while IFS= read -r link; do
    local link_target
    link_target="$(readlink "$link" || true)"

    if [[ "$link_target" == "$REPO_ROOT"/* ]]; then
      restore_or_remove "$link"
    fi
  done < <(find "$target_dir" -maxdepth 1 -mindepth 1 -type l | sort)
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --home)
      [[ $# -ge 2 ]] || fail "--home requires a path"
      TARGET_HOME="$2"
      BACKUP_BASE="${TARGET_HOME}/.local/state/weihung-user-claude/backups"
      shift 2
      ;;
    --skip-external)
      SKIP_EXTERNAL=1
      shift
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

while IFS= read -r skill_dir; do
  restore_or_remove "$TARGET_HOME/.agents/skills/$(basename "$skill_dir")"
done < <(find "$SKILLS_DIR" -maxdepth 1 -mindepth 1 -type d | sort)
prune_managed_links "$TARGET_HOME/.agents/skills"
if [[ -L "$TARGET_HOME/.pi/agent/rules" && "$(readlink "$TARGET_HOME/.pi/agent/rules")" == "$REPO_ROOT/rules" ]]; then
  restore_or_remove "$TARGET_HOME/.pi/agent/rules"
fi

pi_args=(uninstall --home "$TARGET_HOME")
if [[ "$SKIP_EXTERNAL" -eq 1 ]]; then pi_args+=(--skip-external); fi
python3 "$REPO_ROOT/scripts/pi-target.py" "${pi_args[@]}"

rmdir "$TARGET_HOME/.agents/skills" "$TARGET_HOME/.agents" 2>/dev/null || true

log "Uninstall complete."
