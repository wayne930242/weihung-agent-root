#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
HOOKS_CONFIG="$REPO_ROOT/config/claude-hooks.json"
SETTINGS_CONFIG="$REPO_ROOT/config/claude-settings.json"
CODEX_CONFIG="$REPO_ROOT/config/codex-managed.toml"
CLAUDE_AGENTS_DIR="$REPO_ROOT/claude/agents"
CLAUDE_COMMANDS_DIR="$REPO_ROOT/claude/commands"
CLAUDE_HOOKS_DIR="$REPO_ROOT/claude/hooks"
CODEX_AGENTS_DIR="$REPO_ROOT/codex/agents"
CODEX_RULES_DIR="$REPO_ROOT/codex/rules"
CODEX_HOOKS_DIR="$REPO_ROOT/codex/hooks"
SHARED_DIR="$REPO_ROOT/shared"
SKILLS_DIR="$REPO_ROOT/skills"
RULES_DIR="$REPO_ROOT/rules"

TARGET_HOME="${HOME}"
BACKUP_BASE="${TARGET_HOME}/.local/state/weihung-user-claude/backups"

usage() {
  cat <<'EOF'
Usage: bash scripts/uninstall.sh [--home PATH]

Uninstall flow:
  - restore managed files from the latest backup directory when a backup exists
  - otherwise remove repo-managed symlinks
  - remove repo-managed Claude hook entries from ~/.claude/settings.json
  - drop current managed Claude settings when they still hold the installed value
  - drop managed top-level keys from ~/.codex/config.toml when they still hold the installed value

This script does not modify ~/.gemini/config/config.json.
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

remove_retired_repo_link() {
  local dest="$1"
  local former_src="$2"

  if [[ -L "$dest" ]] && [[ "$(readlink "$dest")" == "$former_src" ]]; then
    rm "$dest"
    log "Removed retired repository link $dest"
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

cleanup_empty_dirs() {
  local dirs=(
    "$TARGET_HOME/.claude/agents"
    "$TARGET_HOME/.claude/commands"
    "$TARGET_HOME/.claude/hooks"
    "$TARGET_HOME/.claude/shared"
    "$TARGET_HOME/.claude/skills"
    "$TARGET_HOME/.claude/plugins"
    "$TARGET_HOME/.codex/agents"
    "$TARGET_HOME/.codex/rules"
    "$TARGET_HOME/.codex/hooks"
    "$TARGET_HOME/.codex/skills"
    "$TARGET_HOME/.gemini/config/skills"
    "$TARGET_HOME/.gemini/config/rules"
    "$TARGET_HOME/.gemini/config/plugins"
    "$TARGET_HOME/.gemini/config"
    "$TARGET_HOME/.gemini"
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

  python3 - "$settings_path" "$HOOKS_CONFIG" "$CLAUDE_HOOKS_DIR" "$TARGET_HOME" <<'PY'
import json
import re
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
fragment_path = Path(sys.argv[2])
managed_hooks_dir = Path(sys.argv[3])
target_home = sys.argv[4]

settings = json.loads(settings_path.read_text(encoding="utf-8"))
fragment = json.loads(fragment_path.read_text(encoding="utf-8"))

# Every script under claude/hooks/ is about to be removed, so its registration has
# to go too - even when the entry no longer matches the current fragment because an
# older release registered it. A surviving entry fails with exit 127 on every event.
managed_names = {path.name for path in managed_hooks_dir.glob("*.sh")}
managed_pattern = re.compile(
    r"(?:\$HOME|%s)/\.claude/hooks/([A-Za-z0-9._-]+)" % re.escape(target_home)
)


def is_managed(command):
    return any(name in managed_names for name in managed_pattern.findall(command))


fragment_hooks = fragment.get("hooks", {})
current_hooks = settings.get("hooks")
if isinstance(current_hooks, dict):
    for event_name in list(current_hooks):
        current_entries = current_hooks.get(event_name)
        if not isinstance(current_entries, list):
            continue

        fragment_serialized = {
            json.dumps(entry, sort_keys=True)
            for entry in fragment_hooks.get(event_name, [])
        }

        filtered_entries = []
        for entry in current_entries:
            if json.dumps(entry, sort_keys=True) in fragment_serialized:
                continue
            kept = [h for h in entry.get("hooks", []) if not is_managed(h.get("command", ""))]
            if kept:
                filtered_entries.append({**entry, "hooks": kept})

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

clean_managed_settings() {
  local settings_path="$1"
  local fragment_path="$2"

  if [[ ! -f "$settings_path" || ! -f "$fragment_path" ]]; then
    return
  fi

  python3 - "$settings_path" "$fragment_path" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
fragment_path = Path(sys.argv[2])

settings = json.loads(settings_path.read_text(encoding="utf-8"))
fragment = json.loads(fragment_path.read_text(encoding="utf-8"))

for key, value in fragment.items():
    if settings.get(key) == value:
        settings.pop(key, None)

if settings:
    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
else:
    settings_path.unlink()
PY

  log "Cleaned managed Claude settings from $settings_path"
}

clean_codex_config() {
  local config_path="$1"
  local fragment_path="$2"

  if [[ ! -f "$config_path" || ! -f "$fragment_path" ]]; then
    return
  fi

  python3 - "$config_path" "$fragment_path" <<'PY'
import re
import sys
import tomllib
from pathlib import Path

config_path = Path(sys.argv[1])
fragment = tomllib.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
lines = config_path.read_text(encoding="utf-8").splitlines()


def holds_installed_value(line, values):
    try:
        parsed = tomllib.loads(line)
    except tomllib.TOMLDecodeError:
        return False
    return len(parsed) == 1 and any(parsed.get(key) == value for key, value in values.items())


def header_table(line):
    match = re.match(r"^\s*\[\s*([^\[\]]+?)\s*\]\s*(#.*)?$", line)
    return match.group(1) if match else None


# Split into sections: the top-level lines, then each header with its body.
sections = [[None, []]]
for line in lines:
    if line.lstrip().startswith("["):
        sections.append([line, []])
    else:
        sections[-1][1].append(line)

kept = []
for header, body in sections:
    table = None if header is None else header_table(header)
    values = fragment if header is None else fragment.get(table)
    if isinstance(values, dict):
        body = [line for line in body if not holds_installed_value(line, values)]
        # Drop a managed table that the cleanup left empty.
        if header is not None and not any(line.strip() for line in body):
            continue
    kept += ([header] if header is not None else []) + body
while kept and not kept[-1].strip():
    kept.pop()
if any(line.strip() for line in kept):
    config_path.write_text("\n".join(kept) + "\n", encoding="utf-8")
else:
    config_path.unlink()
PY

  log "Cleaned managed Codex settings from $config_path"
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

remove_retired_repo_link \
  "$TARGET_HOME/.codex/agents/safety-reviewer.toml" \
  "$REPO_ROOT/codex/agents/safety-reviewer.toml"

remove_retired_repo_link \
  "$TARGET_HOME/.claude/skills/tdd" \
  "$REPO_ROOT/skills/tdd"
remove_retired_repo_link \
  "$TARGET_HOME/.codex/skills/tdd" \
  "$REPO_ROOT/skills/tdd"
remove_retired_repo_link \
  "$TARGET_HOME/.gemini/config/skills/tdd" \
  "$REPO_ROOT/skills/tdd"
remove_retired_repo_link \
  "$TARGET_HOME/.claude/skills/refining-from-complaints" \
  "$REPO_ROOT/skills/refining-from-complaints"
remove_retired_repo_link \
  "$TARGET_HOME/.codex/skills/refining-from-complaints" \
  "$REPO_ROOT/skills/refining-from-complaints"
remove_retired_repo_link \
  "$TARGET_HOME/.gemini/config/skills/refining-from-complaints" \
  "$REPO_ROOT/skills/refining-from-complaints"

# Clean first: a hook entry in settings.json must never outlive a removed script,
# or every matching event fails with exit 127.
clean_managed_settings "$TARGET_HOME/.claude/settings.json" "$SETTINGS_CONFIG"
clean_codex_config "$TARGET_HOME/.codex/config.toml" "$CODEX_CONFIG"
clean_claude_settings "$TARGET_HOME/.claude/settings.json"

restore_or_remove "$TARGET_HOME/.claude/CLAUDE.md"
restore_or_remove "$TARGET_HOME/.claude/statusline.sh"
restore_or_remove "$TARGET_HOME/.codex/AGENTS.md"
restore_or_remove "$TARGET_HOME/.codex/hooks.json"
restore_or_remove "$TARGET_HOME/.gemini/config/AGENTS.md"
restore_or_remove "$TARGET_HOME/.gemini/config/GEMINI.md"
restore_or_remove "$TARGET_HOME/.gemini/config/skills.json"

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.claude/agents/$(basename "$file")"
done < <(find "$CLAUDE_AGENTS_DIR" -maxdepth 1 -type f -name '*.md' | sort)

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.claude/commands/$(basename "$file")"
done < <(find "$CLAUDE_COMMANDS_DIR" -maxdepth 1 -type f -name '*.md' | sort)

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.claude/hooks/$(basename "$file")"
done < <(find "$CLAUDE_HOOKS_DIR" -maxdepth 1 -type f -name '*.sh' | sort)

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.claude/shared/$(basename "$file")"
done < <(find "$SHARED_DIR" -maxdepth 1 -type f -name '*.md' | sort)

while IFS= read -r skill_dir; do
  restore_or_remove "$TARGET_HOME/.claude/skills/$(basename "$skill_dir")"
  restore_or_remove "$TARGET_HOME/.codex/skills/$(basename "$skill_dir")"
  restore_or_remove "$TARGET_HOME/.gemini/config/skills/$(basename "$skill_dir")"
done < <(find "$SKILLS_DIR" -maxdepth 1 -mindepth 1 -type d | sort)

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.codex/agents/$(basename "$file")"
done < <(find "$CODEX_AGENTS_DIR" -maxdepth 1 -type f -name '*.toml' | sort)

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.codex/rules/$(basename "$file")"
done < <(find "$CODEX_RULES_DIR" -maxdepth 1 -type f -name '*.rules' | sort)

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.gemini/config/rules/$(basename "$file")"
done < <(find "$RULES_DIR" -maxdepth 1 -type f -name '*.md' | sort)

while IFS= read -r file; do
  restore_or_remove "$TARGET_HOME/.codex/hooks/$(basename "$file")"
done < <(find "$CODEX_HOOKS_DIR" -maxdepth 1 -type f -name '*.sh' | sort)

prune_managed_links "$TARGET_HOME/.claude/skills"
prune_managed_links "$TARGET_HOME/.gemini/config/skills"
prune_managed_links "$TARGET_HOME/.codex/skills"
prune_managed_links "$TARGET_HOME/.claude/agents"
prune_managed_links "$TARGET_HOME/.claude/commands"
prune_managed_links "$TARGET_HOME/.claude/hooks"
prune_managed_links "$TARGET_HOME/.claude/shared"
prune_managed_links "$TARGET_HOME/.codex/agents"
prune_managed_links "$TARGET_HOME/.codex/rules"
prune_managed_links "$TARGET_HOME/.gemini/config/rules"
prune_managed_links "$TARGET_HOME/.codex/hooks"


cleanup_empty_dirs

log "Uninstall complete."
