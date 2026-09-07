#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
HOOKS_CONFIG="$REPO_ROOT/config/claude-hooks.json"
SETTINGS_CONFIG="$REPO_ROOT/config/claude-settings.json"
CLAUDE_AGENTS_DIR="$REPO_ROOT/claude/agents"
CLAUDE_COMMANDS_DIR="$REPO_ROOT/claude/commands"
CLAUDE_HOOKS_DIR="$REPO_ROOT/claude/hooks"
CODEX_AGENTS_DIR="$REPO_ROOT/codex/agents"
CODEX_RULES_DIR="$REPO_ROOT/codex/rules"
CODEX_HOOKS_DIR="$REPO_ROOT/codex/hooks"
SHARED_DIR="$REPO_ROOT/shared"
SKILLS_DIR="$REPO_ROOT/skills"

TARGET_HOME="${HOME}"
FORCE=0
BACKUP_ROOT=""

usage() {
  cat <<'EOF'
Usage: bash scripts/install.sh [--home PATH] [--force]

Installs this repository as the source of truth for:
  - ~/.claude/CLAUDE.md
  - ~/.claude/shared/*.md
  - ~/.claude/skills/*/
  - ~/.claude/agents/*.md
  - ~/.claude/commands/*.md
  - ~/.claude/hooks/*.sh
  - ~/.claude/statusline.sh
  - ~/.codex/AGENTS.md
  - ~/.codex/skills/*/
  - ~/.codex/agents/*.toml
  - ~/.codex/rules/*.rules
  - ~/.codex/hooks.json
  - ~/.codex/hooks/*.sh

It also merges two fragments into ~/.claude/settings.json:
  - config/claude-hooks.json    hooks and statusLine
  - config/claude-settings.json Opus 1M main and cross-session settings

Codex agents use their role-specific GPT-5.6 model selections.

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

remove_retired_repo_link() {
  local dest="$1"
  local former_src="$2"

  if [[ -L "$dest" ]] && [[ "$(readlink "$dest")" == "$former_src" ]]; then
    rm "$dest"
    log "Removed retired repository link $dest"
  fi
}

merge_claude_settings() {
  local settings_path="$1"
  local fragment_path="$2"

  python3 - "$settings_path" "$fragment_path" <<'PY'
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
  log "Merged $(basename "$fragment_path") into $settings_path"
}

migrate_legacy_model_settings() {
  local settings_path="$1"

  if [[ ! -f "$settings_path" ]]; then
    return
  fi

  local migration_result
  migration_result="$(python3 - "$settings_path" <<'PY'
import json
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
settings = json.loads(settings_path.read_text(encoding="utf-8"))
env = settings.get("env")
changes = []

if isinstance(env, dict) and env.get("CLAUDE_CODE_SUBAGENT_MODEL") == "sonnet":
    env.pop("CLAUDE_CODE_SUBAGENT_MODEL")
    if not env:
        settings.pop("env")
    changes.append("legacy worker model pin")

if settings.get("advisorModel") == "opus":
    settings.pop("advisorModel")
    changes.append("former Opus advisor setting")

if not changes:
    raise SystemExit(0)

settings_path.write_text(
    json.dumps(settings, indent=2, ensure_ascii=False) + "\n",
    encoding="utf-8",
)
print("\n".join(changes))
PY
)"

  if [[ -n "$migration_result" ]]; then
    while IFS= read -r change; do
      log "Migrated $change from $settings_path"
    done <<< "$migration_result"
  fi
}

prune_orphan_hooks() {
  local settings_path="$1"
  local target_home="$2"

  if [[ ! -f "$settings_path" ]]; then
    return
  fi

  python3 - "$settings_path" "$target_home" <<'PY'
import json
import os
import re
import sys
from pathlib import Path

settings_path = Path(sys.argv[1])
target_home = sys.argv[2]

settings = json.loads(settings_path.read_text(encoding="utf-8"))
hooks = settings.get("hooks")
if not isinstance(hooks, dict):
    raise SystemExit(0)

pattern = re.compile(r"(?:\$HOME|%s)/\.claude/hooks/[A-Za-z0-9._-]+" % re.escape(target_home))
dropped = []


def runnable(command):
    for match in pattern.findall(command):
        script = match.replace("$HOME", target_home, 1)
        if not os.access(script, os.X_OK):
            dropped.append(script)
            return False
    return True


for event_name in list(hooks):
    entries = hooks[event_name]
    if not isinstance(entries, list):
        continue

    kept_entries = []
    for entry in entries:
        kept = [h for h in entry.get("hooks", []) if runnable(h.get("command", ""))]
        if kept:
            kept_entries.append({**entry, "hooks": kept})

    if kept_entries:
        hooks[event_name] = kept_entries
    else:
        hooks.pop(event_name)

if not hooks:
    settings.pop("hooks", None)

if dropped:
    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\n".join("Dropped hook entry for missing script: %s" % s for s in dropped))
PY
}

report_optional_plugins() {
  local settings_path="$TARGET_HOME/.claude/settings.json"

  if [[ -f "$settings_path" ]] && python3 -c '
import json
import sys

settings = json.load(open(sys.argv[1], encoding="utf-8"))
sys.exit(0 if settings.get("enabledPlugins", {}).get("codex@openai-codex") else 1)
' "$settings_path" 2>/dev/null; then
    return
  fi

  cat <<'EOF'

Optional: the Codex plugin backs the cross-model routing in CLAUDE.md.
Install it from a Claude Code session:

  /plugin marketplace add openai/codex-plugin-cc
  /plugin install codex@openai-codex
  /reload-plugins
  /codex:setup
EOF
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
mkdir -p "$TARGET_HOME/.claude/hooks" "$TARGET_HOME/.claude/shared" "$TARGET_HOME/.claude/skills"
mkdir -p "$TARGET_HOME/.claude/commands"
mkdir -p "$TARGET_HOME/.codex/agents" "$TARGET_HOME/.codex/rules" "$TARGET_HOME/.codex/hooks" "$TARGET_HOME/.codex/skills"

remove_retired_repo_link \
  "$TARGET_HOME/.codex/agents/safety-reviewer.toml" \
  "$REPO_ROOT/codex/agents/safety-reviewer.toml"

remove_retired_repo_link \
  "$TARGET_HOME/.claude/skills/tdd" \
  "$REPO_ROOT/skills/tdd"
remove_retired_repo_link \
  "$TARGET_HOME/.codex/skills/tdd" \
  "$REPO_ROOT/skills/tdd"

install_link "$REPO_ROOT/CLAUDE.md" "$TARGET_HOME/.claude/CLAUDE.md"
install_link "$REPO_ROOT/claude/statusline.sh" "$TARGET_HOME/.claude/statusline.sh"
install_link "$REPO_ROOT/AGENTS.md" "$TARGET_HOME/.codex/AGENTS.md"
install_link "$REPO_ROOT/codex/hooks.json" "$TARGET_HOME/.codex/hooks.json"

while IFS= read -r agent_file; do
  install_link "$agent_file" "$TARGET_HOME/.claude/agents/$(basename "$agent_file")"
done < <(find "$CLAUDE_AGENTS_DIR" -maxdepth 1 -type f -name '*.md' | sort)

while IFS= read -r command_file; do
  install_link "$command_file" "$TARGET_HOME/.claude/commands/$(basename "$command_file")"
done < <(find "$CLAUDE_COMMANDS_DIR" -maxdepth 1 -type f -name '*.md' | sort)

while IFS= read -r hook_file; do
  install_link "$hook_file" "$TARGET_HOME/.claude/hooks/$(basename "$hook_file")"
done < <(find "$CLAUDE_HOOKS_DIR" -maxdepth 1 -type f -name '*.sh' | sort)

while IFS= read -r shared_file; do
  install_link "$shared_file" "$TARGET_HOME/.claude/shared/$(basename "$shared_file")"
done < <(find "$SHARED_DIR" -maxdepth 1 -type f -name '*.md' | sort)

while IFS= read -r skill_dir; do
  install_link "$skill_dir" "$TARGET_HOME/.claude/skills/$(basename "$skill_dir")"
done < <(find "$SKILLS_DIR" -maxdepth 1 -mindepth 1 -type d | sort)

while IFS= read -r skill_dir; do
  install_link "$skill_dir" "$TARGET_HOME/.codex/skills/$(basename "$skill_dir")"
done < <(find "$SKILLS_DIR" -maxdepth 1 -mindepth 1 -type d | sort)

while IFS= read -r agent_file; do
  install_link "$agent_file" "$TARGET_HOME/.codex/agents/$(basename "$agent_file")"
done < <(find "$CODEX_AGENTS_DIR" -maxdepth 1 -type f -name '*.toml' | sort)

while IFS= read -r rule_file; do
  install_link "$rule_file" "$TARGET_HOME/.codex/rules/$(basename "$rule_file")"
done < <(find "$CODEX_RULES_DIR" -maxdepth 1 -type f -name '*.rules' | sort)

while IFS= read -r hook_file; do
  install_link "$hook_file" "$TARGET_HOME/.codex/hooks/$(basename "$hook_file")"
done < <(find "$CODEX_HOOKS_DIR" -maxdepth 1 -type f -name '*.sh' | sort)

# Merge last: a hook entry in settings.json must never outlive a missing script,
# or every matching event fails with exit 127.
migrate_legacy_model_settings "$TARGET_HOME/.claude/settings.json"
merge_claude_settings "$TARGET_HOME/.claude/settings.json" "$HOOKS_CONFIG"
merge_claude_settings "$TARGET_HOME/.claude/settings.json" "$SETTINGS_CONFIG"

# The merge is additive, so a hook this repo used to manage stays registered after
# it leaves config/claude-hooks.json. Drop any ~/.claude/hooks entry whose script is
# gone; otherwise every matching event fails with exit 127.
prune_orphan_hooks "$TARGET_HOME/.claude/settings.json" "$TARGET_HOME"

log "Install complete."
report_optional_plugins
