#!/usr/bin/env bash
# Stop hook: surface weihung-user-claude changes that no other machine can see yet.
# Fires once per session so it stays a reminder rather than a per-turn nag.

set -uo pipefail

payload_file="$(mktemp)"
trap 'rm -f "$payload_file"' EXIT
cat > "$payload_file" 2>/dev/null || true

self="${BASH_SOURCE[0]}"
[[ -L "$self" ]] && self="$(readlink "$self")"
repo_root="$(cd -- "$(dirname -- "$self")/../.." && pwd)"

git -C "$repo_root" rev-parse --git-dir >/dev/null 2>&1 || exit 0

session_id="$(python3 -c '
import json, sys
try:
    print(json.load(open(sys.argv[1], encoding="utf-8")).get("session_id") or "")
except Exception:
    print("")
' "$payload_file")"

if [[ -n "$session_id" ]]; then
  marker_dir="${HOME}/.claude/state/weihung-user-claude/unpushed-warned"
  marker="${marker_dir}/${session_id}"
  [[ -e "$marker" ]] && exit 0
fi

dirty="$(git -C "$repo_root" status --porcelain | grep -c . || true)"
ahead=0
if git -C "$repo_root" rev-parse --abbrev-ref --symbolic-full-name '@{u}' >/dev/null 2>&1; then
  ahead="$(git -C "$repo_root" rev-list --count '@{u}..HEAD')"
fi

msg=""
if [[ "$dirty" -gt 0 ]]; then
  msg="${dirty} 個未 commit 的檔案"
fi
if [[ "$ahead" -gt 0 ]]; then
  [[ -n "$msg" ]] && msg="${msg}、"
  msg="${msg}${ahead} 個未 push 的 commit"
fi

[[ -z "$msg" ]] && exit 0

if [[ -n "$session_id" ]]; then
  mkdir -p "$marker_dir"
  : > "$marker"
fi

python3 -c 'import json,sys; print(json.dumps({"systemMessage": sys.argv[1]}, ensure_ascii=False))' \
  "⚠️ weihung-user-claude 有 ${msg}，別台機器還吃不到"

exit 0
