#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

write_fixture() {
  local root="$1"

  mkdir -p "$root/proj-a/s1/subagents" "$root/proj-b"

  # Main session in the window. m1 streams two lines (text, then one tool),
  # m2 calls two tools, and a compaction follows.
  cat >"$root/proj-a/s1.jsonl" <<'EOF'
{"type":"user","timestamp":"2026-09-10T00:00:00Z","message":{"role":"user","content":"go"}}
{"type":"assistant","timestamp":"2026-09-10T00:00:01Z","message":{"id":"m1","model":"claude-opus-5","content":[{"type":"text","text":"ok"}],"usage":{"input_tokens":0,"cache_creation_input_tokens":100000,"cache_read_input_tokens":0,"output_tokens":1000,"cache_creation":{"ephemeral_1h_input_tokens":100000,"ephemeral_5m_input_tokens":0}}}}
{"type":"assistant","timestamp":"2026-09-10T00:00:02Z","message":{"id":"m1","model":"claude-opus-5","content":[{"type":"tool_use","id":"t1","name":"Bash","input":{}}],"usage":{"input_tokens":0,"cache_creation_input_tokens":100000,"cache_read_input_tokens":0,"output_tokens":1000,"cache_creation":{"ephemeral_1h_input_tokens":100000,"ephemeral_5m_input_tokens":0}}}}
{"type":"assistant","timestamp":"2026-09-10T00:01:00Z","message":{"id":"m2","model":"claude-opus-5","content":[{"type":"tool_use","id":"t2","name":"Read","input":{}}],"usage":{"input_tokens":0,"cache_creation_input_tokens":0,"cache_read_input_tokens":500000,"output_tokens":2000}}}
{"type":"assistant","timestamp":"2026-09-10T00:01:01Z","message":{"id":"m2","model":"claude-opus-5","content":[{"type":"tool_use","id":"t3","name":"Read","input":{}}],"usage":{"input_tokens":0,"cache_creation_input_tokens":0,"cache_read_input_tokens":500000,"output_tokens":2000}}}
{"type":"system","subtype":"compact_boundary","timestamp":"2026-09-10T00:02:00Z"}
EOF

  # Subagent on claude-fable-5-1, whose cache reads bill at 0.025x.
  cat >"$root/proj-a/s1/subagents/agent-x.jsonl" <<'EOF'
{"type":"assistant","timestamp":"2026-09-10T00:00:30Z","message":{"id":"m4","model":"claude-fable-5-1","content":[{"type":"text","text":"done"}],"usage":{"input_tokens":1000,"cache_creation_input_tokens":0,"cache_read_input_tokens":100000,"output_tokens":0}}}
EOF

  # Session entirely before the window: excluded despite a recent mtime.
  cat >"$root/proj-b/s2.jsonl" <<'EOF'
{"type":"assistant","timestamp":"2026-08-01T00:00:00Z","message":{"id":"m3","model":"claude-opus-5","content":[],"usage":{"input_tokens":0,"cache_creation_input_tokens":0,"cache_read_input_tokens":900000,"output_tokens":9000}}}
EOF
}

report_matches_hand_computed_costs() {
  local temp_dir output
  temp_dir="$(mktemp -d)"
  write_fixture "$temp_dir"

  output="$(python3 "$REPO_ROOT/scripts/token-sinks.py" --root "$temp_dir" --since 2026-09-01 --until 2026-09-17)"

  # m1 = 100000*2 + 1000*5 = 205000; m2 = 500000*0.1 + 2000*5 = 60000;
  # m4 = 100000*0.025 + 1000 = 3500; total 268500.
  OUTPUT="$output" python3 - <<'PY' || fail "token-sinks report mismatch"
import os
import re

out = os.environ["OUTPUT"]
expected = [
    r"Sessions: main=1 subagent=1  API calls: 3  compactions: 1",
    r"cache read\s+19\.6%",
    r"cache write\s+74\.5%",
    r"uncached input\s+0\.4%",
    r"output\s+5\.6%",
    r"<=200k\s+77\.7%",
    r"200-400k\s+0\.0%",
    r">400k\s+22\.3%",
    r"Tool-using calls with exactly one tool\s+50\.0%",
    r"Subagent share of cost\s+1\.3%",
    r"Median first-call context\s+main=100,000 subagent=101,000",
    r"100\.0%  proj-a",
    r"calls=2 max context=500k compactions=1  proj-a/s1\.jsonl",
]
missing = [pattern for pattern in expected if not re.search(pattern, out)]
assert not missing, (missing, out)
assert "proj-b" not in out, out
PY

  rm -rf "$temp_dir"
}

run_all_tests() {
  report_matches_hand_computed_costs
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
else
  "$1"
fi
