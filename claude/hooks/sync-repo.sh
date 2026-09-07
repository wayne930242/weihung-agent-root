#!/usr/bin/env bash
# SessionStart hook: fast-forward the weihung-user-claude checkout to origin so a
# new session reads the settings that other machines already pushed.

set -uo pipefail

# Drain the hook payload; the harness writes it whether or not we read it.
cat >/dev/null 2>&1 || true

self="${BASH_SOURCE[0]}"
[[ -L "$self" ]] && self="$(readlink "$self")"
repo_root="$(cd -- "$(dirname -- "$self")/../.." && pwd)"

git -C "$repo_root" rev-parse --git-dir >/dev/null 2>&1 || exit 0

emit() {
  python3 -c 'import json,sys; print(json.dumps({"systemMessage": sys.argv[1]}, ensure_ascii=False))' "$1"
}

# Portable timeout. GNU timeout is absent on a stock macOS, and http.lowSpeed*
# only governs transfer rate, not a remote that never completes its handshake --
# that case blocked for 75s in testing.
git -C "$repo_root" -c http.lowSpeedLimit=1000 -c http.lowSpeedTime=4 \
  fetch --quiet origin >/dev/null 2>&1 &
fetch_pid=$!

waited=0
while [ "$waited" -lt 6 ] && kill -0 "$fetch_pid" 2>/dev/null; do
  sleep 1
  waited=$((waited + 1))
done

if kill -0 "$fetch_pid" 2>/dev/null; then
  kill -TERM "$fetch_pid" 2>/dev/null
  exit 0
fi

# Offline is the common case here, and it is not worth a warning.
wait "$fetch_pid" || exit 0

git -C "$repo_root" rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1 || exit 0

before="$(git -C "$repo_root" rev-parse HEAD)"
remote_head="$(git -C "$repo_root" rev-parse '@{u}')"

[[ "$before" == "$remote_head" ]] && exit 0

if ! git -C "$repo_root" merge-base --is-ancestor "$before" "$remote_head"; then
  emit "⚠️ weihung-user-claude 與 origin 已分岔，未自動同步；本機讀的是舊設定"
  exit 0
fi

if ! git -C "$repo_root" merge --ff-only --quiet "$remote_head" >/dev/null 2>&1; then
  emit "⚠️ weihung-user-claude 無法 fast-forward（工作區可能有未 commit 的改動），未自動同步"
  exit 0
fi

count="$(git -C "$repo_root" rev-list --count "$before..$remote_head")"

# install.sh is idempotent and cheap, so run it on every update rather than
# guessing which commits added files or touched the settings fragments.
if bash "$repo_root/scripts/install.sh" >/dev/null 2>&1; then
  emit "🔄 weihung-user-claude 已更新 ${count} 個 commit（${before:0:7}..${remote_head:0:7}），install.sh 已重跑"
else
  emit "🔄 weihung-user-claude 已更新 ${count} 個 commit，但 install.sh 失敗；請手動執行 scripts/install.sh"
fi

exit 0
