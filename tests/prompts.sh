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

SKILL_DIR="$REPO_ROOT/skills/leveraging-tasks"

assert_file_contains() {
  local path="$1"
  local needle="$2"

  tr -s '[:space:]' ' ' <"$path" | grep -qF -- "$needle" \
    || fail "$(basename "$path") is missing: $needle"
}

assert_file_lacks() {
  local path="$1"
  local needle="$2"

  tr -s '[:space:]' ' ' <"$path" | grep -qF -- "$needle" \
    && fail "$(basename "$path") still contains: $needle"
  return 0
}

assert_line_budget() {
  local path="$1"
  local budget="$2"
  local actual

  actual="$(wc -l <"$path")"
  (( actual <= budget )) || fail "$(basename "$path") is $actual lines, budget is $budget"
}

mini_spec_keeps_its_load_bearing_rules() {
  local skill="$SKILL_DIR/SKILL.md"

  assert_file_contains "$skill" "**Inline:**"
  assert_file_contains "$skill" "**Durable:**"
  assert_file_contains "$skill" "wait for explicit user confirmation"
  assert_file_contains "$skill" "Production-source editing starts only after this point"
  assert_file_contains "$skill" "\`tdd\` for every programming change"
  assert_file_contains "$skill" "Correctness is agent-owned"
  assert_file_contains "$skill" "never substitutes for missing correctness evidence"
  assert_file_contains "$skill" "no \`tasks.md\`"
  assert_file_contains "$skill" "DEBUGGING.md"
  assert_file_contains "$skill" "MINI-SDD.md"
}

mini_spec_stays_within_its_line_budget() {
  assert_line_budget "$SKILL_DIR/SKILL.md" 75
  assert_line_budget "$SKILL_DIR/MINI-SDD.md" 40
  assert_line_budget "$SKILL_DIR/DEBUGGING.md" 35

  local total
  total="$(cat "$SKILL_DIR"/*.md | wc -l)"
  (( total <= 150 )) || fail "mini-spec surface is $total lines, budget is 150"
}

mini_spec_states_the_persistence_threshold_once() {
  local artifact="$SKILL_DIR/MINI-SDD.md"

  assert_file_lacks "$artifact" "Keep work inline"
  assert_file_lacks "$artifact" "Persistence threshold"
  assert_file_contains "$artifact" "The threshold itself"
}

active_instructions_carry_no_openspec_route() {
  local hits

  hits="$(cd "$REPO_ROOT" && git ls-files -z \
    | tr '\0' '\n' \
    | grep -v '^docs/' \
    | grep -v '^tests/prompts.sh$' \
    | tr '\n' '\0' \
    | xargs -0 grep -lil -e openspec -e opsx || true)"

  [[ -z "$hits" ]] || fail "active files still route to OpenSpec: $hits"
}

run_all_tests() {
  codex_refinement_triggers_only_on_new_design
  codex_refinement_skips_spec_driven_frontend_work
  codex_refinement_is_no_longer_mandatory_for_user_facing_work
  codex_refinement_keeps_its_scope_limits
  mini_spec_keeps_its_load_bearing_rules
  mini_spec_stays_within_its_line_budget
  mini_spec_states_the_persistence_threshold_once
  active_instructions_carry_no_openspec_route
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
else
  "$1"
fi
