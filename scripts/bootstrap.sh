#!/usr/bin/env bash

set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/wayne930242/weihung-user-claude}"
TARGET_HOME="${HOME}"
TARGET_REPO_DIR="${TARGET_REPO_DIR:-$TARGET_HOME/.claude/projects/weihung-user-claude}"

usage() {
  cat <<'EOF'
Usage: bash scripts/bootstrap.sh [install args...]

Bootstrap flow:
  1. Clone or update weihung-user-claude into ~/.claude/projects/weihung-user-claude
  2. Run scripts/install.sh from the cloned repository

Environment overrides:
  REPO_URL         Source repository URL or local path
  TARGET_REPO_DIR  Clone destination
EOF
}

log() {
  printf '%s\n' "$*"
}

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
  usage
  exit 0
fi

mkdir -p "$(dirname "$TARGET_REPO_DIR")"

if [[ -d "$TARGET_REPO_DIR/.git" ]]; then
  log "Updating existing repo at $TARGET_REPO_DIR"
  git -C "$TARGET_REPO_DIR" remote set-url origin "$REPO_URL"
  git -C "$TARGET_REPO_DIR" fetch origin
  current_branch="$(git -C "$TARGET_REPO_DIR" branch --show-current)"
  if [[ -z "$current_branch" ]]; then
    current_branch="main"
  fi
  git -C "$TARGET_REPO_DIR" checkout "$current_branch" >/dev/null 2>&1 || true
  git -C "$TARGET_REPO_DIR" pull --ff-only origin "$current_branch"
elif [[ -e "$TARGET_REPO_DIR" ]]; then
  fail "$TARGET_REPO_DIR exists but is not a git repository"
else
  log "Cloning repo into $TARGET_REPO_DIR"
  git clone "$REPO_URL" "$TARGET_REPO_DIR"
fi

log "Running installer from $TARGET_REPO_DIR"
bash "$TARGET_REPO_DIR/scripts/install.sh" "$@"
