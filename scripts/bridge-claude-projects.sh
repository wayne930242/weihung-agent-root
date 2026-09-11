#!/usr/bin/env bash

set -euo pipefail

DRY_RUN=0
FORCE=0
QUIET=0
TARGET_PATHS=()

usage() {
  cat <<'HELP'
Usage: bash scripts/bridge-claude-projects.sh [OPTIONS] [DIR...]

Bridge existing Claude Code projects for Antigravity by establishing symlinks:
  - AGENTS.md -> CLAUDE.md (when CLAUDE.md exists)
  - .agents/skills -> ../.claude/skills (when .claude/skills exists)

Arguments:
  DIR...            Project directories or parent directories containing projects
                    (default: current working directory)

Options:
  --dry-run         Display actions without modifying the filesystem
  --force           Overwrite conflicting non-symlink targets after backing them up
  --quiet           Suppress informational messages, only report errors
  -h, --help        Show this help message
HELP
}

log() {
  if [[ "$QUIET" -ne 1 ]]; then
    printf '%s\n' "$*"
  fi
}

warn() {
  printf 'Warning: %s\n' "$*" >&2
}

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)
      DRY_RUN=1
      shift
      ;;
    --force)
      FORCE=1
      shift
      ;;
    --quiet)
      QUIET=1
      shift
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      TARGET_PATHS+=("$1")
      shift
      ;;
  esac
done

if [[ ${#TARGET_PATHS[@]} -eq 0 ]]; then
  TARGET_PATHS=(".")
fi

bridge_project() {
  local proj="$1"

  # 1. Bridge CLAUDE.md -> AGENTS.md
  local claude_md="$proj/CLAUDE.md"
  local agents_md="$proj/AGENTS.md"
  if [[ -f "$claude_md" ]]; then
    if [[ -L "$agents_md" ]]; then
      local current_target
      current_target="$(readlink "$agents_md")"
      if [[ "$current_target" == "CLAUDE.md" || "$current_target" == "$claude_md" ]]; then
        log "  OK: $agents_md -> CLAUDE.md"
      else
        if [[ "$FORCE" -eq 1 ]]; then
          if [[ "$DRY_RUN" -eq 1 ]]; then
            log "  [dry-run] Would replace symlink $agents_md -> CLAUDE.md"
          else
            ln -sf "CLAUDE.md" "$agents_md"
            log "  Replaced: $agents_md -> CLAUDE.md"
          fi
        else
          warn "Skipping $agents_md (points to unexpected target: $current_target). Pass --force to replace."
        fi
      fi
    elif [[ -e "$agents_md" ]]; then
      if [[ "$FORCE" -eq 1 ]]; then
        if [[ "$DRY_RUN" -eq 1 ]]; then
          log "  [dry-run] Would back up $agents_md and link to CLAUDE.md"
        else
          mv "$agents_md" "${agents_md}.bak"
          ln -s "CLAUDE.md" "$agents_md"
          log "  Backed up to ${agents_md}.bak and linked $agents_md -> CLAUDE.md"
        fi
      else
        warn "Skipping $agents_md (already exists as regular file). Pass --force to replace."
      fi
    else
      if [[ "$DRY_RUN" -eq 1 ]]; then
        log "  [dry-run] Would link $agents_md -> CLAUDE.md"
      else
        ln -s "CLAUDE.md" "$agents_md"
        log "  Linked: $agents_md -> CLAUDE.md"
      fi
    fi
  fi

  # 2. Bridge .claude/skills -> .agents/skills
  local claude_skills="$proj/.claude/skills"
  local agents_skills="$proj/.agents/skills"
  if [[ -d "$claude_skills" ]]; then
    if [[ -L "$agents_skills" ]]; then
      local current_target
      current_target="$(readlink "$agents_skills")"
      if [[ "$current_target" == "../.claude/skills" || "$current_target" == "$claude_skills" ]]; then
        log "  OK: $agents_skills -> ../.claude/skills"
      else
        if [[ "$FORCE" -eq 1 ]]; then
          if [[ "$DRY_RUN" -eq 1 ]]; then
            log "  [dry-run] Would replace symlink $agents_skills -> ../.claude/skills"
          else
            ln -sfn "../.claude/skills" "$agents_skills"
            log "  Replaced: $agents_skills -> ../.claude/skills"
          fi
        else
          warn "Skipping $agents_skills (points to unexpected target: $current_target). Pass --force to replace."
        fi
      fi
    elif [[ -e "$agents_skills" ]]; then
      if [[ "$FORCE" -eq 1 ]]; then
        if [[ "$DRY_RUN" -eq 1 ]]; then
          log "  [dry-run] Would back up $agents_skills and link to ../.claude/skills"
        else
          mv "$agents_skills" "${agents_skills}.bak"
          ln -s "../.claude/skills" "$agents_skills"
          log "  Backed up to ${agents_skills}.bak and linked $agents_skills -> ../.claude/skills"
        fi
      else
        warn "Skipping $agents_skills (already exists as real path). Pass --force to replace."
      fi
    else
      if [[ "$DRY_RUN" -eq 1 ]]; then
        log "  [dry-run] Would create directory $(dirname "$agents_skills") and link $agents_skills -> ../.claude/skills"
      else
        mkdir -p "$(dirname "$agents_skills")"
        ln -s "../.claude/skills" "$agents_skills"
        log "  Linked: $agents_skills -> ../.claude/skills"
      fi
    fi
  fi
}

is_project_root() {
  local dir="$1"
  [[ -f "$dir/CLAUDE.md" || -d "$dir/.claude" ]]
}

find_and_bridge() {
  local target="$1"
  if [[ ! -d "$target" ]]; then
    warn "Directory does not exist: $target"
    return
  fi

  if is_project_root "$target"; then
    log "Processing project: $target"
    bridge_project "$target"
    return
  fi

  local found_any=0
  while IFS= read -r proj_dir; do
    [[ -n "$proj_dir" ]] || continue
    log "Processing project: $proj_dir"
    bridge_project "$proj_dir"
    found_any=1
  done < <(find "$target" -mindepth 1 -maxdepth 3 -type d \( -name .git -o -name node_modules -o -name .venv -o -name venv \) -prune -o -type f -name 'CLAUDE.md' -exec dirname {} + | sort -u)

  if [[ "$found_any" -eq 0 ]]; then
    log "No Claude Code projects found under: $target"
  fi
}

for path in "${TARGET_PATHS[@]}"; do
  find_and_bridge "$path"
done

log "Done."
