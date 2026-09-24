#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
KEEPER="$REPO_ROOT/scripts/codex-plugin-cache-keeper.py"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

make_version() {
  mkdir -p "$1/hooks"
  printf '#!/bin/sh\n' >"$1/hooks/production-safety-hook"
}

run_keeper() {
  python3 "$KEEPER" --cache-root "$1/cache" --state "$1/state.json"
}

upgrade_keeps_previous_version_resolvable() {
  local root plugin
  root="$(mktemp -d)"
  plugin="$root/cache/market/tool"
  make_version "$plugin/0.6.6"
  run_keeper "$root" >/dev/null

  rm -rf "$plugin/0.6.6"
  make_version "$plugin/0.6.7"
  run_keeper "$root" >/dev/null

  [[ -L "$plugin/0.6.6" ]] || fail "removed 0.6.6 was not linked"
  [[ "$(readlink "$plugin/0.6.6")" == "0.6.7" ]] || fail "0.6.6 does not point at 0.6.7"
  [[ -f "$plugin/0.6.6/hooks/production-safety-hook" ]] || fail "hook path under 0.6.6 does not resolve"
  rm -rf "$root"
}

reinstall_in_progress_is_left_alone() {
  local root plugin
  root="$(mktemp -d)"
  plugin="$root/cache/market/tool"
  make_version "$plugin/0.6.6"
  make_version "$plugin/0.6.7"
  run_keeper "$root" >/dev/null

  rm -rf "$plugin/0.6.7"
  run_keeper "$root" >/dev/null

  [[ ! -e "$plugin/0.6.7" && ! -L "$plugin/0.6.7" ]] || fail "linked the newest version while it was being reinstalled"
  rm -rf "$root"
}

chained_upgrade_repoints_broken_link() {
  local root plugin
  root="$(mktemp -d)"
  plugin="$root/cache/market/tool"
  make_version "$plugin/0.6.7"
  ln -s 0.6.7 "$plugin/0.6.6"
  run_keeper "$root" >/dev/null

  rm -rf "$plugin/0.6.7"
  make_version "$plugin/0.6.10"
  run_keeper "$root" >/dev/null

  [[ "$(readlink "$plugin/0.6.6")" == "0.6.10" ]] || fail "broken 0.6.6 link was not re-pointed at 0.6.10"
  [[ "$(readlink "$plugin/0.6.7")" == "0.6.10" ]] || fail "removed 0.6.7 was not linked to 0.6.10"
  rm -rf "$root"
}

removed_plugin_is_forgotten() {
  local root
  root="$(mktemp -d)"
  make_version "$root/cache/market/tool/1.0.0"
  run_keeper "$root" >/dev/null

  rm -rf "$root/cache/market/tool"
  run_keeper "$root" >/dev/null

  [[ ! -e "$root/cache/market/tool" ]] || fail "recreated a plugin that was uninstalled"
  python3 -c 'import json,sys; sys.exit("market/tool" in json.load(open(sys.argv[1])))' "$root/state.json" \
    || fail "state still tracks the uninstalled plugin"
  rm -rf "$root"
}

upgrade_keeps_previous_version_resolvable
reinstall_in_progress_is_left_alone
chained_upgrade_repoints_broken_link
removed_plugin_is_forgotten
printf 'codex_plugin_cache_keeper: all tests passed\n'
