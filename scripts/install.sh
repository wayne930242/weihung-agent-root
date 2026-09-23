#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
HOOKS_CONFIG="$REPO_ROOT/config/claude-hooks.json"
SETTINGS_CONFIG="$REPO_ROOT/config/claude-settings.json"
CODEX_CONFIG="$REPO_ROOT/config/codex-managed.toml"
CLAUDE_AGENTS_DIR="$REPO_ROOT/claude/agents"
CLAUDE_HOOKS_DIR="$REPO_ROOT/claude/hooks"
CODEX_AGENTS_DIR="$REPO_ROOT/codex/agents"
CODEX_RULES_DIR="$REPO_ROOT/codex/rules"
CODEX_HOOKS_DIR="$REPO_ROOT/codex/hooks"
SHARED_DIR="$REPO_ROOT/shared"
SKILLS_DIR="$REPO_ROOT/skills"
RULES_DIR="$REPO_ROOT/rules"
GEMINI_SKILLS_CONFIG="$REPO_ROOT/config/gemini-skills.json"
CODEBASE_MEMORY_INSTALL_URL="https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh"

TARGET_HOME="${HOME}"
FORCE=0
SKIP_EXTERNAL=0
BACKUP_ROOT=""

usage() {
  cat <<'EOF'
Usage: bash scripts/install.sh [--home PATH] [--force] [--skip-external]

Installs this repository as the source of truth for:
  - ~/.claude/CLAUDE.md
  - ~/.claude/shared/*.md
  - ~/.claude/skills/*/
  - ~/.claude/agents/*.md
  - ~/.claude/hooks/*.sh
  - ~/.claude/statusline.sh
  - ~/.codex/AGENTS.md
  - ~/.agents/skills/*/ (Codex personal skills)
  - ~/.codex/agents/*.toml
  - ~/.codex/rules/*.rules
  - ~/.codex/hooks.json
  - ~/.codex/hooks/*.sh
  - ~/.gemini/config/AGENTS.md
  - ~/.gemini/config/GEMINI.md
  - ~/.gemini/config/skills.json
  - ~/.gemini/config/skills/*/
  - ~/.gemini/config/rules/*.md

It also merges two fragments into ~/.claude/settings.json:
  - config/claude-hooks.json    hooks and statusLine
  - config/claude-settings.json Opus 5.5 1M high main, 300k auto-compact, cross-session, and empty commit/PR attribution settings

It sets only the keys of config/codex-managed.toml (300k auto-compact, the
[tui] status line, and the explicitly disabled plugins) in ~/.codex/config.toml
and keeps the rest of that file as written.

Codex agents use their role-specific GPT-5.6 model selections.

It installs codebase-memory-mcp into ~/.local/bin when that binary is missing,
which the code-discovery protocol in CLAUDE.md and AGENTS.md depends on.

It installs or upgrades the agent-browser CLI with Homebrew (npm on hosts
without Homebrew, such as WSL), downloads its Chrome, and adds the official
agent-browser skill to ~/.agents/skills (Codex) and ~/.claude/skills.

Pass --skip-external to install configuration only.

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

is_in_list() {
  local target="$1"
  shift
  local item
  for item in "$@"; do
    if [[ "$item" == "$target" ]]; then
      return 0
    fi
  done
  return 1
}

prune_managed_entries() {
  local target_dir="$1"
  shift
  local allowed=("$@")

  [[ -d "$target_dir" ]] || return 0

  while IFS= read -r link; do
    local link_name
    link_name="$(basename "$link")"
    local link_target
    link_target="$(readlink "$link" || true)"

    if [[ "$link_target" == "$REPO_ROOT"/* ]]; then
      if ! is_in_list "$link_name" ${allowed[@]+"${allowed[@]}"} || [[ ! -e "$link" ]]; then
        rm "$link"
        log "Pruned retired managed link $link"
      fi
    fi
  done < <(find "$target_dir" -maxdepth 1 -mindepth 1 -type l | sort)
}

# Codex reads personal skills from ~/.agents/skills. Directory copies left there
# under a repository skill name are stale snapshots, so they move to the backup
# before the repository links take their place.
retire_skill_copies() {
  local skills_dir="$1"
  shift
  local name

  for name in "$@"; do
    if [[ -e "$skills_dir/$name" && ! -L "$skills_dir/$name" ]]; then
      backup_target "$skills_dir/$name"
    fi
  done
}

# codebase-memory-mcp writes its skill to both ~/.codex/skills and
# ~/.agents/skills, and Codex loads each copy. The ~/.agents/skills copy stays;
# the ~/.codex/skills one moves there when it is the only copy, or to the backup.
consolidate_codex_skill() {
  local name="$1"
  local legacy="$TARGET_HOME/.codex/skills/$name"
  local current="$TARGET_HOME/.agents/skills/$name"

  [[ -e "$legacy" && ! -L "$legacy" ]] || return 0

  if [[ -e "$current" ]]; then
    backup_target "$legacy"
  else
    mv "$legacy" "$current"
    log "Moved $legacy -> $current"
  fi
}

merge_claude_settings() {
  local settings_path="$1"
  local fragment_path="$2"

  python3 - "$settings_path" "$fragment_path" <<'PY'
import json
import re
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

MANAGED_SCRIPT = re.compile(r"/\.claude/hooks/([A-Za-z0-9._-]+)")


def managed_scripts(fragment_hooks):
    names = set()
    for entries in fragment_hooks.values():
        if not isinstance(entries, list):
            continue
        for entry in entries:
            for hook in entry.get("hooks", []):
                names.update(MANAGED_SCRIPT.findall(hook.get("command", "")))
    return names


def merge_hooks(current_hooks, fragment_hooks):
    """Repo-managed registrations are replaced; every other registration stays."""
    names = managed_scripts(fragment_hooks)
    merged_hooks = deepcopy(current_hooks) if isinstance(current_hooks, dict) else {}

    for event_name, fragment_entries in fragment_hooks.items():
        current_entries = merged_hooks.get(event_name)
        kept = []
        if isinstance(current_entries, list):
            for entry in current_entries:
                unmanaged = [
                    hook
                    for hook in entry.get("hooks", [])
                    if not names.intersection(MANAGED_SCRIPT.findall(hook.get("command", "")))
                ]
                if unmanaged:
                    kept.append({**entry, "hooks": unmanaged})
        merged_hooks[event_name] = kept + deepcopy(fragment_entries)

    return merged_hooks


if settings_path.exists():
    current = json.loads(settings_path.read_text(encoding="utf-8"))
else:
    current = {}

fragment = json.loads(fragment_path.read_text(encoding="utf-8"))
merged = deep_merge(current, fragment)
if isinstance(fragment.get("hooks"), dict):
    merged["hooks"] = merge_hooks(current.get("hooks"), fragment["hooks"])
if "env" in current and not isinstance(current["env"], dict):
    # A non-object env is the user's own value; managed keys merge into an
    # object or not at all, so it is never replaced wholesale.
    merged["env"] = current["env"]
settings_path.parent.mkdir(parents=True, exist_ok=True)
settings_path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
PY
  log "Merged $(basename "$fragment_path") into $settings_path"
}

# config.toml stays user-owned: only the fragment's keys are replaced, top-level
# ones at the top and table ones inside their [table] (appended when missing),
# and every other line, table, and comment is kept as written.
merge_codex_config() {
  local config_path="$1"
  local fragment_path="$2"

  python3 - "$config_path" "$fragment_path" <<'PY'
import json
import re
import sys
import tomllib
from pathlib import Path

config_path = Path(sys.argv[1])
fragment = tomllib.loads(Path(sys.argv[2]).read_text(encoding="utf-8"))
lines = config_path.read_text(encoding="utf-8").splitlines() if config_path.exists() else []


def toml_key(key):
    return key if re.fullmatch(r"[A-Za-z0-9_-]+", key) else json.dumps(key)


def table_name(path):
    return ".".join(toml_key(part) for part in path)


def section_body(table):
    # The line range after a table's header, up to the next header; None when absent.
    if table is None:
        start = 0
    else:
        header = re.compile(r"^\s*\[\s*" + re.escape(table) + r"\s*\]\s*(#.*)?$")
        start = next((i + 1 for i, line in enumerate(lines) if header.match(line)), None)
        if start is None:
            return None
    end = next((i for i in range(start, len(lines)) if lines[i].lstrip().startswith("[")), len(lines))
    return start, end


def set_keys(path, values):
    table = table_name(path) if path else None
    assigned = [f"{toml_key(key)} = {json.dumps(value)}" for key, value in values.items()]
    body = section_body(table)
    if body is None:
        return lines + ([""] if lines else []) + [f"[{table}]"] + assigned
    start, end = body
    managed_key = re.compile(r"^\s*(" + "|".join(re.escape(toml_key(key)) for key in values) + r")\s*=")
    kept = [line for line in lines[start:end] if not managed_key.match(line)]
    return lines[:start] + assigned + kept + lines[end:]


def managed_tables(values, path=()):
    scalars = {key: value for key, value in values.items() if not isinstance(value, dict)}
    if scalars:
        yield path, scalars
    for key, value in values.items():
        if isinstance(value, dict):
            yield from managed_tables(value, path + (key,))


for path, values in managed_tables(fragment):
    lines = set_keys(path, values)
merged = "\n".join(lines) + "\n"
tomllib.loads(merged)
config_path.parent.mkdir(parents=True, exist_ok=True)
config_path.write_text(merged, encoding="utf-8")
PY
  log "Merged $(basename "$fragment_path") into $config_path"
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

install_codebase_memory_mcp() {
  local binary="$TARGET_HOME/.local/bin/codebase-memory-mcp"

  if [[ -x "$binary" ]]; then
    log "OK: $binary"
    return
  fi

  # The upstream installer downloads a 300 MB binary and registers it with
  # every coding agent it finds, so a sandboxed run says so rather than
  # inferring it: a test drives this script with HOME set to its own fixture,
  # which makes the target home indistinguishable from the real one.
  if [[ "$SKIP_EXTERNAL" -eq 1 ]]; then
    log "Skipping codebase-memory-mcp: --skip-external installs configuration only."
    return
  fi

  log "Installing codebase-memory-mcp from $CODEBASE_MEMORY_INSTALL_URL"
  local status=0
  curl -fsSL "$CODEBASE_MEMORY_INSTALL_URL" | bash || status=$?

  # The installed binary is the outcome that matters. Its own activation step
  # registers the MCP server with every coding agent it finds and exits
  # non-zero when any one of those writes fails, which leaves a working
  # install behind.
  if [[ ! -x "$binary" ]]; then
    log "Warning: codebase-memory-mcp install failed (exit $status). Run it again with:"
    log "  curl -fsSL $CODEBASE_MEMORY_INSTALL_URL | bash"
    return
  fi

  if [[ "$status" -ne 0 ]]; then
    log "Note: codebase-memory-mcp installed; its agent-configuration step exited $status."
  fi

  # That step writes through ~/.codex/AGENTS.md and ~/.codex/hooks.json, which
  # are symlinks into this repository, so it edits tracked files.
  log "Review 'git -C $REPO_ROOT status' before committing: the installer rewrites AGENTS.md and codex/hooks.json."
}

install_agent_browser() {
  if [[ "$SKIP_EXTERNAL" -eq 1 ]]; then
    log "Skipping agent-browser: --skip-external installs configuration only."
    return
  fi

  if command -v brew >/dev/null 2>&1; then
    # An npm global copy under an nvm bin directory precedes Homebrew on PATH
    # and shadows the brew binary with whatever version it was pinned at.
    if command -v npm >/dev/null 2>&1 && npm ls -g agent-browser >/dev/null 2>&1; then
      log "Removing npm global agent-browser in favor of Homebrew"
      npm uninstall -g agent-browser
    fi
    # brew install upgrades an outdated formula in place.
    brew install agent-browser
  elif command -v npm >/dev/null 2>&1; then
    # WSL and other Linux hosts without Homebrew use the official npm package.
    log "Homebrew not found; installing agent-browser with npm"
    npm install -g agent-browser@latest
  else
    log "Warning: agent-browser needs Homebrew or npm. Install one, then re-run this script."
    return
  fi
  hash -r

  if [[ "$(uname -s)" == "Linux" ]]; then
    agent-browser install --with-deps
  else
    agent-browser install
  fi

  install_agent_browser_skill
}

# The official skill is a thin stub that loads its workflow from the installed
# CLI. The skills CLI writes it to ~/.agents/skills, which Codex reads, and links
# it into ~/.claude/skills.
install_agent_browser_skill() {
  local lock="$TARGET_HOME/.agents/.skill-lock.json"
  local dest

  if ! python3 -c '
import json, sys
sys.exit(0 if "agent-browser" in json.load(open(sys.argv[1])).get("skills", {}) else 1)
' "$lock" 2>/dev/null; then
    # The skills CLI overwrites an existing copy without a backup.
    for dest in "$TARGET_HOME/.agents/skills/agent-browser" "$TARGET_HOME/.claude/skills/agent-browser"; do
      if [[ -e "$dest" && ! -L "$dest" ]]; then
        if [[ "$FORCE" -ne 1 ]]; then
          log "Warning: $dest is an unmanaged agent-browser skill. Re-run with --force to back it up and install the official skill."
          return
        fi
        backup_target "$dest"
      fi
    done
  fi

  DISABLE_TELEMETRY=1 npx --yes skills@latest add vercel-labs/agent-browser -g -a claude-code -a codex -y
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

mkdir -p "$TARGET_HOME/.claude/agents" "$TARGET_HOME/.codex"
mkdir -p "$TARGET_HOME/.claude/hooks" "$TARGET_HOME/.claude/shared" "$TARGET_HOME/.claude/skills"
mkdir -p "$TARGET_HOME/.codex/agents" "$TARGET_HOME/.codex/rules" "$TARGET_HOME/.codex/hooks" "$TARGET_HOME/.agents/skills"
mkdir -p "$TARGET_HOME/.gemini/config/skills" "$TARGET_HOME/.gemini/config/rules"

remove_retired_repo_link \
  "$TARGET_HOME/.codex/agents/safety-reviewer.toml" \
  "$REPO_ROOT/codex/agents/safety-reviewer.toml"

remove_retired_repo_link \
  "$TARGET_HOME/.claude/skills/tdd" \
  "$REPO_ROOT/skills/tdd"
remove_retired_repo_link \
  "$TARGET_HOME/.gemini/config/skills/tdd" \
  "$REPO_ROOT/skills/tdd"
remove_retired_repo_link \
  "$TARGET_HOME/.claude/skills/refining-from-complaints" \
  "$REPO_ROOT/skills/refining-from-complaints"
remove_retired_repo_link \
  "$TARGET_HOME/.gemini/config/skills/refining-from-complaints" \
  "$REPO_ROOT/skills/refining-from-complaints"
remove_retired_repo_link \
  "$TARGET_HOME/.claude/skills/leveraging-tasks" \
  "$REPO_ROOT/skills/leveraging-tasks"
remove_retired_repo_link \
  "$TARGET_HOME/.gemini/config/skills/leveraging-tasks" \
  "$REPO_ROOT/skills/leveraging-tasks"

root_skills=()
while IFS= read -r skill_dir; do
  root_skills+=("$(basename "$skill_dir")")
done < <(find "$SKILLS_DIR" -maxdepth 1 -mindepth 1 \( -type d -o -type l \) | sort)

claude_agents=()
while IFS= read -r agent_file; do
  claude_agents+=("$(basename "$agent_file")")
done < <(find "$CLAUDE_AGENTS_DIR" -maxdepth 1 -type f -name '*.md' | sort)

claude_hooks=()
while IFS= read -r hook_file; do
  claude_hooks+=("$(basename "$hook_file")")
done < <(find "$CLAUDE_HOOKS_DIR" -maxdepth 1 -type f -name '*.sh' | sort)

shared_docs=()
while IFS= read -r shared_file; do
  shared_docs+=("$(basename "$shared_file")")
done < <(find "$SHARED_DIR" -maxdepth 1 -type f -name '*.md' | sort)

codex_agents=()
while IFS= read -r agent_file; do
  codex_agents+=("$(basename "$agent_file")")
done < <(find "$CODEX_AGENTS_DIR" -maxdepth 1 -type f -name '*.toml' | sort)

codex_rules=()
while IFS= read -r rule_file; do
  codex_rules+=("$(basename "$rule_file")")
done < <(find "$CODEX_RULES_DIR" -maxdepth 1 -type f -name '*.rules' | sort)

gemini_rules=()
while IFS= read -r rule_file; do
  gemini_rules+=("$(basename "$rule_file")")
done < <(find "$RULES_DIR" -maxdepth 1 -type f -name '*.md' | sort)

codex_hooks=()
while IFS= read -r hook_file; do
  codex_hooks+=("$(basename "$hook_file")")
done < <(find "$CODEX_HOOKS_DIR" -maxdepth 1 -type f -name '*.sh' | sort)

prune_managed_entries "$TARGET_HOME/.claude/skills" "${root_skills[@]}"
prune_managed_entries "$TARGET_HOME/.gemini/config/skills" "${root_skills[@]}"
prune_managed_entries "$TARGET_HOME/.agents/skills" "${root_skills[@]}"
# Retired install targets: every repository link there is pruned.
prune_managed_entries "$TARGET_HOME/.codex/skills"
prune_managed_entries "$TARGET_HOME/.claude/commands"
rmdir "$TARGET_HOME/.claude/commands" 2>/dev/null || true
retire_skill_copies "$TARGET_HOME/.agents/skills" "${root_skills[@]}" tdd refining-from-complaints leveraging-tasks
prune_managed_entries "$TARGET_HOME/.claude/agents" "${claude_agents[@]}"
prune_managed_entries "$TARGET_HOME/.claude/hooks" "${claude_hooks[@]}"
prune_managed_entries "$TARGET_HOME/.claude/shared" "${shared_docs[@]}"
prune_managed_entries "$TARGET_HOME/.codex/agents" "${codex_agents[@]}"
prune_managed_entries "$TARGET_HOME/.codex/rules" "${codex_rules[@]}"
prune_managed_entries "$TARGET_HOME/.gemini/config/rules" "${gemini_rules[@]}"
prune_managed_entries "$TARGET_HOME/.codex/hooks" "${codex_hooks[@]}"

install_link "$REPO_ROOT/CLAUDE.md" "$TARGET_HOME/.claude/CLAUDE.md"
install_link "$REPO_ROOT/claude/statusline.sh" "$TARGET_HOME/.claude/statusline.sh"
install_link "$REPO_ROOT/AGENTS.md" "$TARGET_HOME/.codex/AGENTS.md"
install_link "$REPO_ROOT/codex/hooks.json" "$TARGET_HOME/.codex/hooks.json"
install_link "$REPO_ROOT/AGENTS.md" "$TARGET_HOME/.gemini/config/AGENTS.md"
install_link "$REPO_ROOT/AGENTS.md" "$TARGET_HOME/.gemini/config/GEMINI.md"
install_link "$GEMINI_SKILLS_CONFIG" "$TARGET_HOME/.gemini/config/skills.json"

for agent_name in "${claude_agents[@]}"; do
  install_link "$CLAUDE_AGENTS_DIR/$agent_name" "$TARGET_HOME/.claude/agents/$agent_name"
done

for hook_name in "${claude_hooks[@]}"; do
  install_link "$CLAUDE_HOOKS_DIR/$hook_name" "$TARGET_HOME/.claude/hooks/$hook_name"
done

for shared_name in "${shared_docs[@]}"; do
  install_link "$SHARED_DIR/$shared_name" "$TARGET_HOME/.claude/shared/$shared_name"
done

for skill_name in "${root_skills[@]}"; do
  install_link "$SKILLS_DIR/$skill_name" "$TARGET_HOME/.claude/skills/$skill_name"
  install_link "$SKILLS_DIR/$skill_name" "$TARGET_HOME/.agents/skills/$skill_name"
  install_link "$SKILLS_DIR/$skill_name" "$TARGET_HOME/.gemini/config/skills/$skill_name"
done

for agent_name in "${codex_agents[@]}"; do
  install_link "$CODEX_AGENTS_DIR/$agent_name" "$TARGET_HOME/.codex/agents/$agent_name"
done

for rule_name in "${codex_rules[@]}"; do
  install_link "$CODEX_RULES_DIR/$rule_name" "$TARGET_HOME/.codex/rules/$rule_name"
done

for rule_name in "${gemini_rules[@]}"; do
  install_link "$RULES_DIR/$rule_name" "$TARGET_HOME/.gemini/config/rules/$rule_name"
done

for hook_name in "${codex_hooks[@]}"; do
  install_link "$CODEX_HOOKS_DIR/$hook_name" "$TARGET_HOME/.codex/hooks/$hook_name"
done


# Merge last: a hook entry in settings.json must never outlive a missing script,
# or every matching event fails with exit 127.
migrate_legacy_model_settings "$TARGET_HOME/.claude/settings.json"
merge_claude_settings "$TARGET_HOME/.claude/settings.json" "$HOOKS_CONFIG"
merge_claude_settings "$TARGET_HOME/.claude/settings.json" "$SETTINGS_CONFIG"
merge_codex_config "$TARGET_HOME/.codex/config.toml" "$CODEX_CONFIG"

# The merge is additive, so a hook this repo used to manage stays registered after
# it leaves config/claude-hooks.json. Drop any ~/.claude/hooks entry whose script is
# gone; otherwise every matching event fails with exit 127.
prune_orphan_hooks "$TARGET_HOME/.claude/settings.json" "$TARGET_HOME"

install_codebase_memory_mcp
consolidate_codex_skill codebase-memory
install_agent_browser

log "Install complete."
report_optional_plugins
