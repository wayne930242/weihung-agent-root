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

  assert_block_contains "$block" "依 model-preference-profile.md 明確指定模型與 effort"
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

  assert_file_contains "$skill" "ADAAV: Align → Advance → Anchor → Act → Verify"
  assert_file_contains "$skill" "Advance carries Decision → Spec → Design"
  assert_file_contains "$skill" "**Inline:**"
  assert_file_contains "$skill" "**Durable:**"
  assert_file_contains "$skill" "Alignment:"
  assert_file_contains "$skill" "Reality anchor:"
  assert_file_contains "$skill" "target project's native practices"
  assert_file_contains "$skill" "chosen reality anchor"
  assert_file_contains "$skill" "no \`tasks.md\`"
  assert_file_contains "$skill" "DEBUGGING.md"
  assert_file_contains "$skill" "MINI-SDD.md"
}

mini_spec_advances_from_a_grounded_decision() {
  local skill="$SKILL_DIR/SKILL.md"
  local artifact="$SKILL_DIR/MINI-SDD.md"
  local grill="$REPO_ROOT/skills/grill-with-docs/SKILL.md"

  assert_file_contains "$skill" "Invoke \`grill-with-docs\` for every durable Decision step"
  assert_file_contains "$skill" "no open decision blocks observable behavior"
  assert_file_contains "$artifact" "## \`decision.md\`"
  assert_file_contains "$artifact" "Question | Answer | Basis | Status"
  assert_file_contains "$artifact" "\`grounded\`, \`confirmed\`, or \`open\`"
  assert_file_contains "$artifact" "already contains \`requirements.md\`"
  assert_file_contains "$grill" "write every consequential question"
  assert_file_contains "$grill" "When the document has no open consequential decision, return it directly"
  assert_file_contains "$grill" "Invoke \`grilling\` only for the open user-owned frontier"
}

root_prompts_carry_the_exact_positive_writing_principle() {
  local principle="提示詞、文件與文章應直接陳述期望行為，避免不必要的防禦性用語。"

  assert_file_contains "$REPO_ROOT/CLAUDE.md" "$principle"
  assert_file_contains "$REPO_ROOT/AGENTS.md" "$principle"
}

root_prompts_require_prompts_in_english() {
  local rule="All prompts and agent instructions must be in English."

  assert_file_contains "$REPO_ROOT/CLAUDE.md" "$rule"
  assert_file_contains "$REPO_ROOT/AGENTS.md" "$rule"
}

human_feedback_corrects_at_the_root() {
  local skill="$REPO_ROOT/skills/human-feedback/SKILL.md"

  [[ ! -e "$REPO_ROOT/skills/refining-from-complaints" ]] \
    || fail "the retired refining-from-complaints skill is back"

  assert_file_contains "$skill" "the person's observed experience and the need left unmet"
  assert_file_contains "$skill" "justification added to a response or document as a workaround signal"
  assert_file_contains "$skill" "root cause → positive correction"
  assert_file_contains "$skill" "Attend to the problem the person has, ahead of the fix they propose"
  assert_file_contains "$skill" "It lands on the causal decision"
  assert_file_contains "$skill" "A defensive guard belongs where the input is genuinely untrusted"
  assert_file_contains "$skill" "A fallback or special case belongs where its branch is a real case of the domain"
}

human_feedback_is_reachable_from_verification_and_routing() {
  local skill="$SKILL_DIR/SKILL.md"

  assert_file_contains "$skill" "those criteria cover UI or a human-use scenario, ask the user whether to run a \`human-feedback\` pass"
  assert_file_contains "$REPO_ROOT/CLAUDE.md" "Human feedback on working output → \`human-feedback\`"
  assert_file_contains "$REPO_ROOT/AGENTS.md" "Human feedback on working output -> \`human-feedback\`"
}

root_prompts_trigger_the_source_change_graph() {
  local trigger="Source-changing work invokes \`leveraging-tasks\` and states its Alignment and Reality anchor before the first production edit."

  assert_file_contains "$REPO_ROOT/CLAUDE.md" "$trigger"
  assert_file_contains "$REPO_ROOT/AGENTS.md" "$trigger"
}

claude_model_routing_is_canonical() {
  local prompt="$REPO_ROOT/CLAUDE.md"

  assert_file_contains "$prompt" "# Model Work Routing"
  assert_file_contains "$prompt" "Carry simple work from a direct user instruction yourself."
  assert_file_contains "$prompt" "Delegate other fragmentary tasks through Straw Boss or a subagent."
  assert_file_lacks "$prompt" "Delegate every fragmentary task through Straw Boss or a subagent."
  assert_file_contains "$prompt" "Use Straw Boss when the task needs a managed app workroom"
  assert_file_contains "$prompt" "Use a subagent for a self-contained fragment"
  assert_file_contains "$prompt" 'skills/managing-model-preferences/model-preference-profile.md'
  assert_file_contains "$REPO_ROOT/AGENTS.md" 'skills/managing-model-preferences/model-preference-profile.md'
  assert_file_lacks "$prompt" 'claude-fable-5-1'
  assert_file_lacks "$prompt" 'gpt-5.6-'
  assert_file_lacks "$prompt" 'select `sonnet`'
  assert_file_contains "$prompt" 'repair it in `~/projects/straw-boss`'
  assert_file_contains "$prompt" "bump and push the plugin"
  assert_file_contains "$prompt" 'run `bash scripts/install.sh`'
}

orchestrator_authority_handoff_is_user_gated() {
  local prompt="$REPO_ROOT/CLAUDE.md"

  assert_file_contains "$prompt" "# Orchestrator 權限移交"
  assert_file_contains "$prompt" 'handoff-orchestrator'
  assert_file_contains "$prompt" 'docs/roles.md'
  assert_file_contains "$prompt" '使用者的明確指定'
}

mini_spec_route_declares_inline_or_durable() {
  local skill="$SKILL_DIR/SKILL.md"

  assert_file_contains "$skill" "Declare the change **Inline** or **Durable** before the first production edit"
  assert_file_contains "$skill" "Escalate to durable when the request carries material ambiguity"
  assert_file_contains "$skill" "expands scope, or requests a spec first"
}

mini_spec_ratify_records_authority_to_edit() {
  local skill="$SKILL_DIR/SKILL.md"
  local artifact="$SKILL_DIR/MINI-SDD.md"

  assert_file_contains "$skill" "Inline work follows Alignment with these two lines"
  assert_file_contains "$skill" "They are required output"
  assert_file_contains "$skill" "Inline — Contract: <one sentence of the observable behavior after the change>"
  assert_file_contains "$skill" "Authorization: <the user's explicit source-change request>"
  assert_file_contains "$skill" "Approval already given is not requested again"
  assert_file_contains "$skill" "creates or resumes its folder before it specifies anything; that folder is its declaration"
  assert_file_contains "$skill" "Persist the durable contract in \`spec.md\` under \`Status: proposed\` before presenting"
  assert_file_contains "$skill" "\`proposed\` keeps production source untouched"
  assert_file_contains "$skill" "Only the user's approving reply sets"
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
  assert_line_budget "$SKILL_DIR/SKILL.md" 102
  assert_line_budget "$SKILL_DIR/MINI-SDD.md" 60
  assert_line_budget "$SKILL_DIR/DEBUGGING.md" 35

  local total
  total="$(cat "$SKILL_DIR"/*.md | wc -l)"
  (( total <= 197 )) || fail "mini-spec surface is $total lines, budget is 197"
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
    | while IFS= read -r -d '' file; do
        case "$file" in
          docs/*|tests/prompts.sh) continue ;;
        esac
        [[ -f "$file" ]] || continue
        grep -Eil -e openspec -e opsx "$file" || true
      done)"

  [[ -z "$hits" ]] || fail "active files still route to OpenSpec: $hits"
}

run_all_tests() {
  codex_refinement_triggers_only_on_new_design
  codex_refinement_skips_spec_driven_frontend_work
  codex_refinement_is_no_longer_mandatory_for_user_facing_work
  codex_refinement_keeps_its_scope_limits
  mini_spec_keeps_its_load_bearing_rules
  mini_spec_advances_from_a_grounded_decision
  root_prompts_carry_the_exact_positive_writing_principle
  root_prompts_require_prompts_in_english
  human_feedback_corrects_at_the_root
  human_feedback_is_reachable_from_verification_and_routing
  root_prompts_trigger_the_source_change_graph
  claude_model_routing_is_canonical
  orchestrator_authority_handoff_is_user_gated
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
