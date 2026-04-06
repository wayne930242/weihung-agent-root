#!/usr/bin/env bash

set -euo pipefail

state_dir="${HOME}/.claude/state/weihung-user-claude"
log_file="${state_dir}/hooks.jsonl"
payload_file="$(mktemp)"
trap 'rm -f "$payload_file"' EXIT

cat > "$payload_file"
mkdir -p "$state_dir"

python3 - "$log_file" "$payload_file" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

log_path = sys.argv[1]
payload_path = Path(sys.argv[2])
payload = json.loads(payload_path.read_text(encoding="utf-8"))

entry = {
    "timestamp": datetime.now(timezone.utc).isoformat(),
    "event": payload.get("hook_event_name", "Notification"),
    "session_id": payload.get("session_id"),
    "cwd": payload.get("cwd"),
    "message": payload.get("message"),
    "transcript_path": payload.get("transcript_path"),
}

with open(log_path, "a", encoding="utf-8") as fh:
    fh.write(json.dumps(entry, ensure_ascii=True) + "\n")
PY
