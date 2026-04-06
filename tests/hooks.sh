#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

notification_hook_logs_payload() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  HOME="$temp_dir/home" bash "$REPO_ROOT/hooks/log-notification.sh" <<'EOF'
{
  "hook_event_name": "Notification",
  "session_id": "session-123",
  "cwd": "/tmp/project",
  "message": "done",
  "transcript_path": "/tmp/transcript.jsonl"
}
EOF

  python3 - <<PY
import json
from pathlib import Path

log_path = Path("$temp_dir/home/.claude/state/weihung-user-claude/hooks.jsonl")
assert log_path.exists(), log_path
lines = log_path.read_text(encoding="utf-8").strip().splitlines()
assert len(lines) == 1, lines
entry = json.loads(lines[0])
assert entry["event"] == "Notification", entry
assert entry["session_id"] == "session-123", entry
assert entry["cwd"] == "/tmp/project", entry
assert entry["message"] == "done", entry
assert entry["transcript_path"] == "/tmp/transcript.jsonl", entry
PY

  rm -rf "$temp_dir"
}

stop_hook_logs_payload() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  HOME="$temp_dir/home" bash "$REPO_ROOT/hooks/log-stop.sh" <<'EOF'
{
  "hook_event_name": "Stop",
  "session_id": "session-456",
  "cwd": "/tmp/project-2",
  "transcript_path": "/tmp/stop.jsonl"
}
EOF

  python3 - <<PY
import json
from pathlib import Path

log_path = Path("$temp_dir/home/.claude/state/weihung-user-claude/hooks.jsonl")
assert log_path.exists(), log_path
lines = log_path.read_text(encoding="utf-8").strip().splitlines()
assert len(lines) == 1, lines
entry = json.loads(lines[0])
assert entry["event"] == "Stop", entry
assert entry["session_id"] == "session-456", entry
assert entry["cwd"] == "/tmp/project-2", entry
assert entry["transcript_path"] == "/tmp/stop.jsonl", entry
assert entry["stop_hook_active"] is True, entry
PY

  rm -rf "$temp_dir"
}

run_all_tests() {
  notification_hook_logs_payload
  stop_hook_logs_payload
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
else
  "$1"
fi
