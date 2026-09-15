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

retired_complaint_skill_stays_removed() {
  [[ ! -e "$REPO_ROOT/skills/refining-from-complaints" ]] \
    || fail "the retired refining-from-complaints skill is back"
}

human_feedback_is_reachable_from_routing() {
  assert_file_contains "$REPO_ROOT/CLAUDE.md" "Human feedback on working output → \`human-feedback\`"
  assert_file_contains "$REPO_ROOT/AGENTS.md" "Human feedback on working output -> \`human-feedback\`"
}

root_prompts_trigger_the_source_change_graph() {
  local trigger="Source-changing work invokes \`aaaav-do\` and states its Alignment and Reality anchor before the first production edit."

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

active_instructions_carry_no_openspec_route() {
  local hits

  hits="$(cd "$REPO_ROOT" && git ls-files -z \
    | while IFS= read -r -d '' file; do
        case "$file" in
          (docs/*|tests/prompts.sh) continue ;;
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
  root_prompts_carry_the_exact_positive_writing_principle
  root_prompts_require_prompts_in_english
  retired_complaint_skill_stays_removed
  human_feedback_is_reachable_from_routing
  root_prompts_trigger_the_source_change_graph
  claude_model_routing_is_canonical
  orchestrator_authority_handoff_is_user_gated
  mini_spec_is_not_enforced_by_hooks
  mini_spec_has_a_real_agent_behavior_eval
  active_instructions_carry_no_openspec_route
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
else
  "$1"
fi
