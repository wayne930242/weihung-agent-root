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
FORCE=0
BACKUP_ROOT=""

usage() {
  cat <<'EOF'
Usage: bash scripts/install.sh [--home PATH] [--force]

Installs this repository as the source of truth for:
  - ~/.claude/CLAUDE.md
  - ~/.claude/shared/*.md
  - ~/.claude/agents/*.md
  - ~/.claude/hooks/*.sh
  - ~/.claude/statusline.sh
  - ~/.codex/AGENTS.md
  - ~/.codex/agents/*.toml
  - ~/.codex/rules/*.rules
  - ~/.codex/hooks.json
  - ~/.codex/hooks/*.sh

Defaults to failing on conflicts. Pass --force to back up conflicting targets
before replacing them with symlinks.
EOF
}

log() {
  printf '%s\n' "$*"
}

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

ensure_backup_root() {
  if [[ -n "$BACKUP_ROOT" ]]; then
    return
  fi

  local stamp
  stamp="$(date +%Y%m%d-%H%M%S)"
  BACKUP_ROOT="$TARGET_HOME/.local/state/weihung-user-claude/backups/$stamp"
  mkdir -p "$BACKUP_ROOT"
}

backup_target() {
  local dest="$1"
  local rel_dest="${dest#"$TARGET_HOME"/}"

  ensure_backup_root
  mkdir -p "$BACKUP_ROOT/$(dirname "$rel_dest")"
  mv "$dest" "$BACKUP_ROOT/$rel_dest"
  log "Backed up $dest -> $BACKUP_ROOT/$rel_dest"
}

install_link() {
  local src="$1"
  local dest="$2"

  mkdir -p "$(dirname "$dest")"

  if [[ -L "$dest" ]] && [[ "$(readlink "$dest")" == "$src" ]]; then
    log "OK: $dest"
    return
  fi

  if [[ -e "$dest" || -L "$dest" ]]; then
    if [[ "$FORCE" -ne 1 ]]; then
      fail "$dest already exists. Re-run with --force to back it up and replace it."
    fi
    backup_target "$dest"
  fi

  ln -s "$src" "$dest"
  log "Linked $dest -> $src"
}

merge_claude_settings() {
  local settings_path="$1"

  python3 - "$settings_path" "$HOOKS_CONFIG" <<'PY'
import json
import sys
from copy import deepcopy
from pathlib import Path

settings_path = Path(sys.argv[1])
fragment_path = Path(sys.argv[2])

def deep_merge(base, overlay):
    result = deepcopy(base)
    for key, value in overlay.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = deepcopy(value)
    return result

if settings_path.exists():
    current = json.loads(settings_path.read_text(encoding="utf-8"))
else:
    current = {}

fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
merged = deep_merge(current, fragment)
settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY
  log "Merged Claude hooks into $settings_path"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --home)
      [[ $# -ge 2 ]] || fail "--home requires a path"
      TARGET_HOME="$2"
      shift 2
      ;;
    --force)
      FORCE=1
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

mkdir -p "$TARGET_HOME/.claude/agents" "$TARGET_HOME/.codex"
mkdir -p "$TARGET_HOME/.claude/hooks" "$TARGET_HOME/.claude/shared"
mkdir -p "$TARGET_HOME/.codex/agents" "$TARGET_HOME/.codex/rules" "$TARGET_HOME/.codex/hooks"

install_link "$REPO_ROOT/CLAUDE.md" "$TARGET_HOME/.claude/CLAUDE.md"
install_link "$REPO_ROOT/claude/statusline.sh" "$TARGET_HOME/.claude/statusline.sh"
install_link "$REPO_ROOT/AGENTS.md" "$TARGET_HOME/.codex/AGENTS.md"
install_link "$REPO_ROOT/codex/hooks.json" "$TARGET_HOME/.codex/hooks.json"
merge_claude_settings "$TARGET_HOME/.claude/settings.json"

while IFS= read -r agent_file; do
  install_link "$agent_file" "$TARGET_HOME/.claude/agents/$(basename "$agent_file")"
done < <(find "$CLAUDE_AGENTS_DIR" -maxdepth 1 -type f -name '*.md' | sort)

while IFS= read -r hook_file; do
  install_link "$hook_file" "$TARGET_HOME/.claude/hooks/$(basename "$hook_file")"
done < <(find "$CLAUDE_HOOKS_DIR" -maxdepth 1 -type f -name '*.sh' | sort)

while IFS= read -r shared_file; do
  install_link "$shared_file" "$TARGET_HOME/.claude/shared/$(basename "$shared_file")"
done < <(find "$SHARED_DIR" -maxdepth 1 -type f -name '*.md' | sort)

while IFS= read -r agent_file; do
  install_link "$agent_file" "$TARGET_HOME/.codex/agents/$(basename "$agent_file")"
done < <(find "$CODEX_AGENTS_DIR" -maxdepth 1 -type f -name '*.toml' | sort)

while IFS= read -r rule_file; do
  install_link "$rule_file" "$TARGET_HOME/.codex/rules/$(basename "$rule_file")"
done < <(find "$CODEX_RULES_DIR" -maxdepth 1 -type f -name '*.rules' | sort)

while IFS= read -r hook_file; do
  install_link "$hook_file" "$TARGET_HOME/.codex/hooks/$(basename "$hook_file")"
done < <(find "$CODEX_HOOKS_DIR" -maxdepth 1 -type f -name '*.sh' | sort)

log "Install complete."
