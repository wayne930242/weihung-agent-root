#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "$SCRIPT_DIR/.." && pwd)"

WINDOWS_HOME=""
FORCE=0
BACKUP_ROOT=""
SOURCES=()
DESTINATIONS=()

usage() {
  cat <<'EOF'
Usage: bash scripts/install-codex-desktop-wsl.sh [--windows-home PATH] [--force]

Copies this repository's managed Codex assets into the Windows Codex Desktop
home while running from WSL. The default Windows profile is discovered through
cmd.exe and converted with wslpath.

Managed Windows targets:
  - ~/.codex/AGENTS.md
  - ~/.codex/skills/<repository skill>/
  - ~/.codex/agents/*.toml
  - ~/.codex/rules/*.rules
  - ~/.codex/hooks.json
  - ~/.codex/hooks/*.sh

Windows-only .system skills, plugins, config.toml, authentication, history, and
runtime state are not modified. Conflicts fail before installation begins.
Pass --force to move conflicts into a timestamped backup before replacement.

Options:
  --windows-home PATH  Override Windows home discovery. Accepts Windows or WSL paths.
  --force              Back up and replace conflicting managed targets.
  -h, --help           Show this help.
EOF
}

log() {
  printf '%s\n' "$*"
}

fail() {
  printf 'Error: %s\n' "$*" >&2
  exit 1
}

normalize_path() {
  local path="$1"

  if [[ "$path" =~ ^[A-Za-z]:[\\/].* ]]; then
    command -v wslpath >/dev/null 2>&1 || fail "wslpath is required to convert Windows paths"
    wslpath -u "$path"
  else
    printf '%s\n' "$path"
  fi
}

discover_windows_home() {
  command -v cmd.exe >/dev/null 2>&1 || fail "cmd.exe is unavailable; pass --windows-home PATH"
  command -v wslpath >/dev/null 2>&1 || fail "wslpath is unavailable; pass --windows-home with a WSL path"

  local discovered
  local interop_cwd="/mnt/c"
  if [[ ! -d "$interop_cwd" ]]; then
    interop_cwd="/"
  fi
  discovered="$(cd "$interop_cwd" && cmd.exe /d /c "echo %USERPROFILE%" | tr -d '\r' | tail -n 1)"
  [[ -n "$discovered" ]] || fail "could not discover the Windows user profile"
  wslpath -u "$discovered"
}

add_entry() {
  SOURCES+=("$1")
  DESTINATIONS+=("$2")
}

same_content() {
  local src="$1"
  local dest="$2"

  if [[ -f "$src" && -f "$dest" ]]; then
    cmp -s "$src" "$dest"
    return
  fi

  if [[ -d "$src" && -d "$dest" ]]; then
    diff -qr "$src" "$dest" >/dev/null 2>&1
    return
  fi

  return 1
}

ensure_backup_root() {
  if [[ -n "$BACKUP_ROOT" ]]; then
    return
  fi

  local stamp
  stamp="$(date +%Y%m%d-%H%M%S)"
  BACKUP_ROOT="$WINDOWS_HOME/AppData/Local/weihung-user-claude/backups/$stamp"
  mkdir -p "$BACKUP_ROOT"
}

backup_target() {
  local dest="$1"
  local relative_dest="${dest#"$WINDOWS_HOME"/}"

  ensure_backup_root
  mkdir -p "$BACKUP_ROOT/$(dirname "$relative_dest")"
  mv "$dest" "$BACKUP_ROOT/$relative_dest"
  log "Backed up $dest -> $BACKUP_ROOT/$relative_dest"
}

collect_entries() {
  local codex_home="$WINDOWS_HOME/.codex"
  local src

  add_entry "$REPO_ROOT/AGENTS.md" "$codex_home/AGENTS.md"
  add_entry "$REPO_ROOT/codex/hooks.json" "$codex_home/hooks.json"

  while IFS= read -r src; do
    add_entry "$src" "$codex_home/skills/$(basename "$src")"
  done < <(find "$REPO_ROOT/skills" -maxdepth 1 -mindepth 1 -type d | sort)

  local loop_boot_dir="${WEIHUNG_LOOP_BOOT_DIR:-}"
  if [[ -z "$loop_boot_dir" ]]; then
    for candidate in "$REPO_ROOT/../../../weihung-loop-boot" "$HOME/weihung-loop-boot" "/home/weihung/weihung-loop-boot"; do
      if [[ -d "$candidate" ]]; then
        loop_boot_dir="$candidate"
        break
      fi
    done
  fi
  if [[ -n "$loop_boot_dir" && -d "$loop_boot_dir/skills" ]]; then
    while IFS= read -r src; do
      add_entry "$src" "$codex_home/skills/$(basename "$src")"
    done < <(find "$loop_boot_dir/skills" -maxdepth 1 -mindepth 1 -type d | sort)
  fi

  while IFS= read -r src; do
    add_entry "$src" "$codex_home/agents/$(basename "$src")"
  done < <(find "$REPO_ROOT/codex/agents" -maxdepth 1 -type f -name '*.toml' | sort)

  while IFS= read -r src; do
    add_entry "$src" "$codex_home/rules/$(basename "$src")"
  done < <(find "$REPO_ROOT/codex/rules" -maxdepth 1 -type f -name '*.rules' | sort)

  while IFS= read -r src; do
    add_entry "$src" "$codex_home/hooks/$(basename "$src")"
  done < <(find "$REPO_ROOT/codex/hooks" -maxdepth 1 -type f -name '*.sh' | sort)
}

preflight() {
  local index
  local dest

  for index in "${!SOURCES[@]}"; do
    dest="${DESTINATIONS[$index]}"
    if [[ -e "$dest" || -L "$dest" ]]; then
      if same_content "${SOURCES[$index]}" "$dest"; then
        continue
      fi
      if [[ "$FORCE" -ne 1 ]]; then
        fail "$dest conflicts with the repository. Re-run with --force to back it up and replace it."
      fi
    fi
  done
}

install_entries() {
  local index
  local src
  local dest

  for index in "${!SOURCES[@]}"; do
    src="${SOURCES[$index]}"
    dest="${DESTINATIONS[$index]}"

    if [[ -e "$dest" || -L "$dest" ]]; then
      if same_content "$src" "$dest"; then
        log "OK: $dest"
        continue
      fi
      backup_target "$dest"
    fi

    mkdir -p "$(dirname "$dest")"
    cp -a "$src" "$dest"
    log "Installed $dest"
  done
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --windows-home)
      [[ $# -ge 2 ]] || fail "--windows-home requires a path"
      WINDOWS_HOME="$(normalize_path "$2")"
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

if [[ -z "$WINDOWS_HOME" ]]; then
  WINDOWS_HOME="$(discover_windows_home)"
fi

[[ -d "$WINDOWS_HOME" ]] || fail "Windows home does not exist: $WINDOWS_HOME"

collect_entries
preflight
install_entries

log "Codex Desktop install complete: $WINDOWS_HOME/.codex"
