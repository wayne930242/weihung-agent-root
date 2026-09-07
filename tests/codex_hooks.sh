#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

stop_hook_logs_payload() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local output
  output="$(
    HOME="$temp_dir/home" bash "$REPO_ROOT/codex/hooks/log-stop.sh" <<'EOF'
{
  "hook_event_name": "Stop",
  "cwd": "/tmp/codex-project",
  "turn_id": "turn-123",
  "stop_hook_active": true,
  "last_assistant_message": "done"
}
EOF
  )"

  python3 - <<PY
import json
from pathlib import Path

stdout_payload = json.loads("""$output""")
assert stdout_payload["continue"] is True, stdout_payload

log_path = Path("$temp_dir/home/.codex/state/weihung-user-claude/hooks.jsonl")
assert log_path.exists(), log_path
entry = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
assert entry["event"] == "Stop", entry
assert entry["cwd"] == "/tmp/codex-project", entry
assert entry["turn_id"] == "turn-123", entry
assert entry["stop_hook_active"] is True, entry
assert entry["last_assistant_message"] == "done", entry
PY

  rm -rf "$temp_dir"
}

session_start_hook_logs_payload() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local output
  output="$(
    HOME="$temp_dir/home" bash "$REPO_ROOT/codex/hooks/log-session-start.sh" <<'EOF'
{
  "hook_event_name": "SessionStart",
  "source": "startup",
  "cwd": "/tmp/codex-root",
  "session_id": "session-789"
}
EOF
  )"

  python3 - <<PY
import json
from pathlib import Path

stdout_payload = json.loads("""$output""")
assert stdout_payload["continue"] is True, stdout_payload

log_path = Path("$temp_dir/home/.codex/state/weihung-user-claude/hooks.jsonl")
assert log_path.exists(), log_path
entry = json.loads(log_path.read_text(encoding="utf-8").strip().splitlines()[-1])
assert entry["event"] == "SessionStart", entry
assert entry["source"] == "startup", entry
assert entry["cwd"] == "/tmp/codex-root", entry
assert entry["session_id"] == "session-789", entry
PY

  rm -rf "$temp_dir"
}

herdr_session_hook_uses_current_home() {
  python3 - "$REPO_ROOT/codex/hooks.json" <<'PY'
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

config = json.loads(Path(sys.argv[1]).read_text())
commands = [hook["command"] for group in config["hooks"]["SessionStart"]
            for hook in group["hooks"] if "herdr-agent-state.sh" in hook["command"]]
assert len(commands) == 1, commands
with tempfile.TemporaryDirectory(prefix="codex home ") as directory:
    home = Path(directory)
    script = home / ".codex/herdr-agent-state.sh"
    script.parent.mkdir()
    script.write_text('#!/bin/sh\nprintf "%s" "$1"\n')
    result = subprocess.run(commands[0], shell=True, input="{}", text=True,
                            capture_output=True, env={**os.environ, "HOME": str(home)})
    assert result.returncode == 0, result.stderr
    assert result.stdout == "session", result.stdout
PY
}

run_all_tests() {
  herdr_session_hook_uses_current_home
  stop_hook_logs_payload
  session_start_hook_logs_payload
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
else
  "$1"
fi
