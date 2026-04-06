#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BOOTSTRAP_SCRIPT="$REPO_ROOT/scripts/bootstrap.sh"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

assert_symlink_target() {
  local path="$1"
  local expected="$2"

  [[ -L "$path" ]] || fail "expected symlink at $path"
  local actual
  actual="$(readlink "$path")"
  [[ "$actual" == "$expected" ]] || fail "expected $path -> $expected, got $actual"
}

prepare_origin_repo() {
  local temp_dir="$1"
  local bare_repo="$temp_dir/origin.git"

  git clone --bare "$REPO_ROOT" "$bare_repo" >/dev/null 2>&1
  git --git-dir="$bare_repo" symbolic-ref HEAD refs/heads/main

  printf '%s\n' "$bare_repo"
}

fresh_bootstrap_clones_and_installs() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home"

  local origin_repo
  origin_repo="$(prepare_origin_repo "$temp_dir")"

  HOME="$fake_home" REPO_URL="$origin_repo" bash "$BOOTSTRAP_SCRIPT"

  local target_repo="$fake_home/.claude/projects/weihung-user-claude"
  [[ -d "$target_repo/.git" ]] || fail "expected cloned repo at $target_repo"

  assert_symlink_target "$fake_home/.claude/CLAUDE.md" "$target_repo/CLAUDE.md"
  assert_symlink_target "$fake_home/.codex/AGENTS.md" "$target_repo/AGENTS.md"

  rm -rf "$temp_dir"
}

bootstrap_updates_existing_clone() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home"

  local origin_repo
  origin_repo="$(prepare_origin_repo "$temp_dir")"

  HOME="$fake_home" REPO_URL="$origin_repo" bash "$BOOTSTRAP_SCRIPT"

  local target_repo="$fake_home/.claude/projects/weihung-user-claude"
  local first_head
  first_head="$(git -C "$target_repo" rev-parse HEAD)"

  local update_worktree="$temp_dir/update-worktree"
  git clone "$origin_repo" "$update_worktree" >/dev/null 2>&1
  printf '\nbootstrap test update\n' >> "$update_worktree/README.md"
  git -C "$update_worktree" add README.md
  git -C "$update_worktree" commit -m "test: update bootstrap origin" >/dev/null 2>&1
  git -C "$update_worktree" push origin HEAD:main >/dev/null 2>&1

  HOME="$fake_home" REPO_URL="$origin_repo" bash "$BOOTSTRAP_SCRIPT"

  local second_head
  second_head="$(git -C "$target_repo" rev-parse HEAD)"
  [[ "$first_head" != "$second_head" ]] || fail "expected bootstrap to update existing clone"

  rm -rf "$temp_dir"
}

run_all_tests() {
  fresh_bootstrap_clones_and_installs
  bootstrap_updates_existing_clone
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
else
  "$1"
fi
