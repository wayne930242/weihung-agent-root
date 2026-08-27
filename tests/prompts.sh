#!/usr/bin/env bash
#
# Deletion guards for the prompt surface.
#
# These assert that load-bearing lines are still written down and that the
# always-loaded surface stays inside its budget. They are not evidence that an
# agent obeys any of them; that proof is evals/mini-spec-3r.sh, which drives a
# real agent and asserts what it did.

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
  assert_file_contains "$skill" "\`tdd\` for every programming change"
  assert_file_contains "$skill" "Correctness is agent-owned"
  assert_file_contains "$skill" "never substitutes for missing correctness evidence"
  assert_file_contains "$skill" "no \`tasks.md\`"
  assert_file_contains "$skill" "DEBUGGING.md"
  assert_file_contains "$skill" "MINI-SDD.md"
}

mini_spec_route_declares_inline_or_durable() {
  local skill="$SKILL_DIR/SKILL.md"

  assert_file_contains "$skill" "Declare the change **Inline** or **Durable** before the first production edit"
  assert_file_contains "$skill" "Escalate to durable instead when the request carries material ambiguity"
  assert_file_contains "$skill" "expands scope beyond what was asked, or when the user wants to see the spec first"
}

mini_spec_ratify_records_authority_to_edit() {
  local skill="$SKILL_DIR/SKILL.md"
  local artifact="$SKILL_DIR/MINI-SDD.md"

  assert_file_contains "$skill" "Inline work opens its reply with these two lines, then executes"
  assert_file_contains "$skill" "required output, not preamble, and no brevity rule removes them"
  assert_file_contains "$skill" "Inline — Contract: <one sentence of the observable behavior after the change>"
  assert_file_contains "$skill" "Authorization: <the user's explicit source-change request>"
  assert_file_contains "$skill" "Approval already given is not requested again"
  assert_file_contains "$skill" "creates or resumes its folder before it specifies anything; that folder is its declaration"
  assert_file_contains "$skill" "a spec that exists only in the reply is not a durable spec"
  assert_file_contains "$skill" "\`proposed\` forbids production-source editing"
  assert_file_contains "$skill" "Only the user's explicit approving reply sets"
  assert_file_contains "$artifact" "Status: proposed | approved"
  assert_file_contains "$artifact" "Approved at:"
  assert_file_contains "$artifact" "Approved from:"
}

mini_spec_result_is_per_requirement_evidence() {
  local skill="$SKILL_DIR/SKILL.md"
  local artifact="$SKILL_DIR/MINI-SDD.md"

  assert_file_contains "$skill" "Give every requirement in the contract its own \`Requirement | Evidence | Result\` row"
  assert_file_contains "$skill" "\`pass\`, \`fail\`, or \`unknown\`"
  assert_file_contains "$skill" "is not evidence for a requirement nothing exercised"
  assert_file_contains "$artifact" "One \`Requirement | Evidence | Result\` row per requirement"
}

mini_spec_is_not_enforced_by_hooks() {
  local hits

  hits="$(grep -Eil -e 'inline' -e 'durable' -e 'spec\.md' -e 'approved' -e 'authorization' \
    "$REPO_ROOT/config/claude-hooks.json" \
    "$REPO_ROOT/codex/hooks.json" \
    "$REPO_ROOT"/claude/hooks/*.sh \
    "$REPO_ROOT"/codex/hooks/*.sh || true)"

  [[ -z "$hits" ]] || fail "hooks are being used as a workflow engine: $hits"
}

mini_spec_has_a_real_agent_behavior_eval() {
  local eval_script="$REPO_ROOT/evals/mini-spec-3r.sh"

  [[ -x "$eval_script" ]] || fail "evals/mini-spec-3r.sh is missing or not executable"

  local case_name
  for case_name in \
    case_inline_executes_directly \
    case_durable_stops_before_source_edit \
    case_approved_durable_reports_evidence
  do
    grep -q "^$case_name()" "$eval_script" || fail "the behavior eval lost $case_name"
  done
}

mini_spec_stays_within_its_line_budget() {
  assert_line_budget "$SKILL_DIR/SKILL.md" 100
  assert_line_budget "$SKILL_DIR/MINI-SDD.md" 50
  assert_line_budget "$SKILL_DIR/DEBUGGING.md" 35

  local total
  total="$(cat "$SKILL_DIR"/*.md | wc -l)"
  (( total <= 185 )) || fail "mini-spec surface is $total lines, budget is 185"
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
  mini_spec_route_declares_inline_or_durable
  mini_spec_ratify_records_authority_to_edit
  mini_spec_result_is_per_requirement_evidence
  mini_spec_is_not_enforced_by_hooks
  mini_spec_has_a_real_agent_behavior_eval
  mini_spec_stays_within_its_line_budget
  mini_spec_states_the_persistence_threshold_once
  active_instructions_carry_no_openspec_route
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
else
  "$1"
fi
