#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CLAUDE_MD="$REPO_ROOT/CLAUDE.md"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

extract_routing_block() {
  python3 - "$CLAUDE_MD" <<'PY'
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
start = "<!-- straw-boss:agent-routing:start -->"
end = "<!-- straw-boss:agent-routing:end -->"
if start not in text or end not in text:
    sys.exit("routing block markers missing from CLAUDE.md")
sys.stdout.write(text.split(start, 1)[1].split(end, 1)[0])
PY
}

assert_block_contains() {
  local block="$1"
  local needle="$2"

  [[ "$block" == *"$needle"* ]] || fail "routing block is missing: $needle"
}

assert_block_lacks() {
  local block="$1"
  local needle="$2"

  [[ "$block" != *"$needle"* ]] || fail "routing block still contains: $needle"
}

codex_refinement_triggers_only_on_new_design() {
  local block
  block="$(extract_routing_block)"

  assert_block_contains "$block" "only when the completed work introduces new UI/UX design"
  assert_block_contains "$block" "needs design judgment"
  assert_block_contains "$block" "sets a new design direction"
}

codex_refinement_skips_spec_driven_frontend_work() {
  local block
  block="$(extract_routing_block)"

  assert_block_contains "$block" "Do not dispatch this pass when the work only applies an existing layout"
  assert_block_contains "$block" "already specified and only needs implementation to that spec"
  assert_block_contains "$block" "General frontend work is not a trigger by itself"
}

codex_refinement_is_no_longer_mandatory_for_user_facing_work() {
  local block
  block="$(extract_routing_block)"

  assert_block_lacks "$block" "any user-facing deliverable"
  assert_block_lacks "$block" "After completing and verifying"
}

codex_refinement_keeps_its_scope_limits() {
  local block
  block="$(extract_routing_block)"

  assert_block_contains "$block" "Leave model and effort unset"
  assert_block_contains "$block" "repeat the real-interface check until no actionable finding remains"
  assert_block_contains "$block" "does not expand product scope"
}

run_all_tests() {
  codex_refinement_triggers_only_on_new_design
  codex_refinement_skips_spec_driven_frontend_work
  codex_refinement_is_no_longer_mandatory_for_user_facing_work
  codex_refinement_keeps_its_scope_limits
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
else
  "$1"
fi
