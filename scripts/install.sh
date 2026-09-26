#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"
SKILLS_DIR="$REPO_ROOT/skills"
RULES_DIR="$REPO_ROOT/rules"
AGENTS_DIR="$REPO_ROOT/agents"
CODEBASE_MEMORY_INSTALL_URL="https://raw.githubusercontent.com/DeusData/codebase-memory-mcp/main/install.sh"

TARGET_HOME="${HOME}"
FORCE=0
SKIP_EXTERNAL=0
BACKUP_ROOT=""

usage() {
  cat <<'EOF'
Usage: bash scripts/install.sh [--home PATH] [--force] [--skip-external]

Installs this repository's pi setup:
  - ~/.agents/skills/*/        links to skills/
  - ~/.pi/agent/rules          link to rules/
  - ~/.pi/agent/agents         link to agents/
  - ~/.local/bin/codebase-memory-mcp when missing
  - everything scripts/pi-target.py install manages: pi itself, its Herdr
    integration, pi packages, aaaav, this repository's pi package, the
    generated ~/.pi/agent/AGENTS.md, model routing, UI settings,
    codebase-memory, mp-infra (when its checkout exists), and team-toon-tack

Pass --skip-external to install configuration only, without npm, pi, Herdr,
or network installers.

Defaults to failing on conflicts. Pass --force to back up conflicting targets
before replacing them.
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
  BACKUP_ROOT="$TARGET_HOME/.local/state/weihung-agent-root/backups/$stamp"
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

# pi reads personal skills from ~/.agents/skills. Directory copies left there
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

# State and links from the repository's former name move first; the steps below use the new name.
python3 "$REPO_ROOT/scripts/pi-target.py" migrate --home "$TARGET_HOME"

mkdir -p "$TARGET_HOME/.agents/skills"

root_skills=()
while IFS= read -r skill_dir; do
  root_skills+=("$(basename "$skill_dir")")
done < <(find "$SKILLS_DIR" -maxdepth 1 -mindepth 1 \( -type d -o -type l \) | sort)

prune_managed_entries "$TARGET_HOME/.agents/skills" "${root_skills[@]}"
retire_skill_copies "$TARGET_HOME/.agents/skills" "${root_skills[@]}"

for skill_name in "${root_skills[@]}"; do
  install_link "$SKILLS_DIR/$skill_name" "$TARGET_HOME/.agents/skills/$skill_name"
done
install_link "$RULES_DIR" "$TARGET_HOME/.pi/agent/rules"
install_link "$AGENTS_DIR" "$TARGET_HOME/.pi/agent/agents"

install_codebase_memory_mcp

pi_args=(install --home "$TARGET_HOME")
if [[ "$SKIP_EXTERNAL" -eq 1 ]]; then pi_args+=(--skip-external); fi
if [[ "$FORCE" -eq 1 ]]; then pi_args+=(--force); fi
python3 "$REPO_ROOT/scripts/pi-target.py" "${pi_args[@]}"

log "Install complete."
