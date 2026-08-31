#!/usr/bin/env bash
#
# Real agent-behavior eval for the Mini Spec 3R contract.
#
# Each case installs this repository into a throwaway home, drops a throwaway
# project beside it, drives a headless Claude Code agent against those exact
# instructions, and asserts what happened on the filesystem. Assertions read
# files, not the agent's prose, except where the contract requires a specific
# word to be stated.
#
# This is not part of tests/. It costs money, takes minutes, and is not
# deterministic. Run it when the contract text changes.
#
#   bash evals/mini-spec-3r.sh
#   bash evals/mini-spec-3r.sh case_inline_executes_directly
#   EVAL_MODEL=opus bash evals/mini-spec-3r.sh

set -uo pipefail

REPO_ROOT="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
EVAL_MODEL="${EVAL_MODEL:-opus[1m]}"
EVAL_TIMEOUT="${EVAL_TIMEOUT:-900}"
RUN_ROOT="$(mktemp -d -t mini-spec-3r-XXXXXX)"
FAILURES=0

log() { printf '%s\n' "$*"; }
pass() { printf 'PASS: %s\n' "$*"; }
fail() { printf 'FAIL: %s\n' "$*" >&2; FAILURES=$((FAILURES + 1)); }

# --- sandbox -----------------------------------------------------------------

# Installs the repository under a fresh home and lays down a small production
# project. The agent sees exactly the instructions a user gets from install.sh.
new_sandbox() {
  local name="$1"
  local sandbox="$RUN_ROOT/$name"

  mkdir -p "$sandbox/home" "$sandbox/project/src" "$sandbox/project/tests"
  bash "$REPO_ROOT/scripts/install.sh" --home "$sandbox/home" >"$sandbox/install.log" 2>&1 \
    || { printf 'install.sh failed; see %s\n' "$sandbox/install.log" >&2; return 1; }

  if [[ -f "$HOME/.claude/.credentials.json" ]]; then
    cp "$HOME/.claude/.credentials.json" "$sandbox/home/.claude/.credentials.json"
  fi

  cat >"$sandbox/project/README.md" <<'EOF'
# greeter

A tiny CLI. `src/greet.sh` is the production entry point; `tests/greet.sh` is
its check.
EOF

  cat >"$sandbox/project/src/greet.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

printf 'Hello, world\n'
EOF

  cat >"$sandbox/project/tests/greet.sh" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

actual="$(bash "$(dirname "$0")/../src/greet.sh")"
[[ "$actual" == "Hello, world" ]] || { printf 'FAIL: %s\n' "$actual" >&2; exit 1; }
printf 'ok\n'
EOF

  chmod +x "$sandbox/project/src/greet.sh" "$sandbox/project/tests/greet.sh"

  git -C "$sandbox/project" init -q .
  git -C "$sandbox/project" add -A
  git -C "$sandbox/project" -c user.email=eval@local -c user.name=eval commit -qm 'greeter baseline'

  printf '%s\n' "$sandbox"
}

# Runs one headless turn. Streams the whole conversation to a file next to the
# sandbox and echoes its path. The stream is kept rather than the single-result
# envelope because the contract's declaration lines are stated before the agent
# starts working, and a final-message-only view would miss them.
run_turn() {
  local sandbox="$1" label="$2" prompt="$3"
  shift 3
  local stream="$sandbox/$label.jsonl"

  ( cd "$sandbox/project" \
    && CLAUDE_CONFIG_DIR="$sandbox/home/.claude" \
       timeout "$EVAL_TIMEOUT" claude -p "$prompt" \
         --model "$EVAL_MODEL" \
         --output-format stream-json --verbose \
         --permission-mode bypassPermissions \
         --strict-mcp-config --mcp-config '{"mcpServers":{}}' \
         --disallowed-tools WebSearch WebFetch \
         "$@" \
  ) >"$stream" 2>"$sandbox/$label.err"

  if ! jq -se 'map(select(.type == "result")) | length > 0' "$stream" >/dev/null 2>&1; then
    printf 'no usable stream; see %s and %s\n' "$stream" "$sandbox/$label.err" >&2
    return 1
  fi
  printf '%s\n' "$stream"
}

# Everything the agent said across the whole turn, not just its closing message.
result_text() {
  jq -r 'select(.type == "assistant") | .message.content[]?
         | select(.type == "text") | .text' "$1"
}

session_id() { jq -r 'select(.type == "result") | .session_id' "$1" | head -1; }

# --- assertions --------------------------------------------------------------

assert_file_matches() {
  local path="$1" pattern="$2" what="$3"
  if [[ -f "$path" ]] && grep -qiE -- "$pattern" "$path"; then
    pass "$what"
  else
    fail "$what (looked for /$pattern/ in $path)"
  fi
}

assert_file_lacks() {
  local path="$1" pattern="$2" what="$3"
  if [[ -f "$path" ]] && grep -qiE -- "$pattern" "$path"; then
    fail "$what (found /$pattern/ in $path)"
  else
    pass "$what"
  fi
}

assert_text_matches() {
  local text="$1" pattern="$2" what="$3"
  if grep -qiE -- "$pattern" <<<"$text"; then
    pass "$what"
  else
    fail "$what (looked for /$pattern/ in the agent's reply)"
  fi
}

assert_unchanged() {
  local sandbox="$1" path="$2" what="$3"
  if git -C "$sandbox/project" diff --quiet -- "$path" \
     && git -C "$sandbox/project" diff --cached --quiet -- "$path"; then
    pass "$what"
  else
    fail "$what ($path was modified)"
    git -C "$sandbox/project" --no-pager diff -- "$path" >&2
  fi
}

assert_changed() {
  local sandbox="$1" path="$2" what="$3"
  if git -C "$sandbox/project" diff --quiet HEAD -- "$path"; then
    fail "$what ($path is still at baseline)"
  else
    pass "$what"
  fi
}

assert_alignment_and_anchor_precede_source_edit() {
  local stream="$1" what="$2"

  python3 - "$stream" <<'PY' || { fail "$what"; return; }
import json
import re
import sys

seen_alignment = False
seen_anchor = False

for line in open(sys.argv[1], encoding="utf-8"):
    event = json.loads(line)
    if event.get("type") != "assistant":
        continue

    for block in event.get("message", {}).get("content", []):
        if block.get("type") == "text":
            text = block.get("text", "")
            seen_alignment |= re.search(r"(?im)^Alignment:", text) is not None
            seen_anchor |= re.search(r"(?im)^Reality anchor:", text) is not None
            continue

        if block.get("type") != "tool_use":
            continue

        name = block.get("name", "")
        payload = json.dumps(block.get("input", {}), ensure_ascii=False)
        direct_edit = name in {"Edit", "Write", "MultiEdit", "NotebookEdit"}
        shell_edit = name == "Bash" and re.search(
            r"(?:sed\s+-i|perl\s+-pi|tee\b|(?:^|[;&|]\s*)mv\b|(?:^|[;&|]\s*)cp\b|>{1,2})",
            block.get("input", {}).get("command", ""),
        )
        edits_source = "src/greet.sh" in payload and (direct_edit or shell_edit)
        if edits_source:
            raise SystemExit(0 if seen_alignment and seen_anchor else 1)

raise SystemExit(1)
PY

  pass "$what"
}

first_match() { find "$1" -path "$2" -print -quit 2>/dev/null; }

# --- case: inline ------------------------------------------------------------

INLINE_PROMPT='In src/greet.sh, change the greeting from "Hello, world" to "Hello, Mini Spec", and update tests/greet.sh to match. Nothing else.'

case_inline_executes_directly() {
  local sandbox stream reply
  sandbox="$(new_sandbox inline)"
  [[ -n "$sandbox" ]] || { fail "inline: sandbox setup failed"; return; }
  log "--- case_inline_executes_directly ($sandbox)"

  stream="$(run_turn "$sandbox" inline "$INLINE_PROMPT")"
  [[ -n "$stream" ]] || { fail "inline: the agent turn produced no result"; return; }
  reply="$(result_text "$stream")"

  assert_file_matches "$sandbox/project/src/greet.sh" 'Hello, Mini Spec' \
    "inline: the agent edited production source in the same turn"
  assert_text_matches "$reply" 'inline' \
    "inline: the agent declared the change inline"
  assert_text_matches "$reply" 'contract' \
    "inline: the agent stated an observable contract"
  assert_text_matches "$reply" 'authoriz' \
    "inline: the agent recorded the request as its authorization"
  assert_alignment_and_anchor_precede_source_edit "$stream" \
    "inline: Alignment and Reality anchor preceded the production edit"

  if [[ -n "$(first_match "$sandbox/project" '*/docs/specs/*')" ]]; then
    fail "inline: the agent wrote durable artifacts for a low-reuse local change"
  else
    pass "inline: no durable artifacts were written"
  fi
}

# --- case: durable proposal --------------------------------------------------

# Decision-complete on purpose: every product choice is already made, so nothing
# open blocks the specification and the case tests the approval gate rather than
# the requirements interview. What makes it durable is the lasting public
# contract, the stated reuse, and the user asking to see the spec first.
DURABLE_PROMPT='Add a --format option to src/greet.sh. It accepts "text", which is the default and keeps today'"'"'s exact output, and "json", which prints {"message":"Hello, world"}. Accept both "--format json" and "--format=json". Any other value exits non-zero with an error on stderr. Treat that JSON shape as a stable public output contract that other tools will depend on and that we will reuse later, and update tests/greet.sh to cover it. Write the specification and show it to me first, and do not modify anything under src/ until I approve it.'

APPROVAL_PROMPT='Approved. The specification is right — go ahead and implement it, and show me the verification.'

DURABLE_SANDBOX=""
DURABLE_SESSION=""

prepare_durable_proposal() {
  [[ -n "$DURABLE_SANDBOX" ]] && return 0

  local sandbox stream
  sandbox="$(new_sandbox durable)"
  [[ -n "$sandbox" ]] || { fail "durable: sandbox setup failed"; return 1; }
  stream="$(run_turn "$sandbox" propose "$DURABLE_PROMPT")"
  [[ -n "$stream" ]] || { fail "durable: the proposal turn produced no result"; return 1; }

  DURABLE_SANDBOX="$sandbox"
  DURABLE_SESSION="$(session_id "$stream")"
}

case_durable_stops_before_source_edit() {
  prepare_durable_proposal || return
  local sandbox="$DURABLE_SANDBOX" spec
  log "--- case_durable_stops_before_source_edit ($sandbox)"

  assert_unchanged "$sandbox" src/greet.sh \
    "durable: production source is untouched while the spec is unapproved"

  spec="$(first_match "$sandbox/project" '*/docs/specs/*/spec.md')"
  if [[ -z "$spec" ]]; then
    fail "durable: no docs/specs/<date>-<slug>/spec.md was created"
    return
  fi
  pass "durable: a durable spec.md was created at ${spec#"$sandbox/project/"}"

  assert_file_matches "$spec" '^Status:[[:space:]]*proposed' \
    "durable: spec.md carries Status: proposed"
  assert_file_lacks "$spec" '^Status:[[:space:]]*approved' \
    "durable: spec.md is not self-approved"
  assert_file_matches "$spec" '^Approved at:' \
    "durable: spec.md carries the Approved at field"
  assert_file_matches "$spec" '^Approved from:' \
    "durable: spec.md carries the Approved from field"
}

# --- case: durable after approval -------------------------------------------

case_approved_durable_reports_evidence() {
  prepare_durable_proposal || return
  local sandbox="$DURABLE_SANDBOX" spec verification rows bad
  log "--- case_approved_durable_reports_evidence ($sandbox)"

  run_turn "$sandbox" approve "$APPROVAL_PROMPT" --resume "$DURABLE_SESSION" >/dev/null \
    || { fail "approved: the approval turn produced no result"; return; }

  spec="$(first_match "$sandbox/project" '*/docs/specs/*/spec.md')"
  if [[ -z "$spec" ]]; then
    fail "approved: the durable spec.md disappeared"
    return
  fi

  assert_file_matches "$spec" '^Status:[[:space:]]*approved' \
    "approved: the user's reply moved Status to approved"
  assert_file_matches "$spec" '^Approved at:[[:space:]]*[0-9]{4}-[0-9]{2}-[0-9]{2}' \
    "approved: Approved at records a date"
  assert_file_matches "$spec" '^Approved from:[[:space:]]*\S' \
    "approved: Approved from records the approving reply"

  assert_changed "$sandbox" src/greet.sh \
    "approved: production source was implemented after approval"

  verification="$(first_match "$sandbox/project" '*/docs/specs/*/verification.md')"
  if [[ -z "$verification" ]]; then
    fail "approved: no verification.md was written"
    return
  fi

  assert_file_matches "$verification" 'Requirement.*\|.*Evidence.*\|.*Result' \
    "approved: verification.md maps requirements to evidence and result"

  # Inspect only the table introduced by the Requirement/Evidence/Result header;
  # later evidence tables may have their own domain-specific columns.
  read -r rows bad < <(python3 - "$verification" <<'PY'
import re
import sys

lines = open(sys.argv[1], encoding="utf-8").read().splitlines()
header = re.compile(r"^\|\s*requirement\s*\|\s*evidence\s*\|\s*result\s*\|$", re.I)
separator = re.compile(r"^\|(?:\s*:?-+:?\s*\|){3}$")
verdict = re.compile(r"\|\s*(pass|fail|unknown)\s*\|$", re.I)

rows = 0
bad = 0
inside = False
for line in lines:
    if header.match(line):
        inside = True
        continue
    if not inside:
        continue
    if not line.startswith("|"):
        if rows:
            break
        continue
    if separator.match(line):
        continue
    rows += 1
    bad += verdict.search(line) is None

print(rows, bad)
PY
)
  if (( rows >= 2 )); then
    pass "approved: $rows requirements carry an individual pass/fail/unknown verdict"
  else
    fail "approved: found $rows per-requirement verdict rows, expected at least 2"
    sed -n '1,60p' "$verification" >&2
  fi

  if (( bad == 0 )); then
    pass "approved: every verdict is one of pass, fail, or unknown"
  else
    fail "approved: $bad requirement row(s) carry a verdict outside pass/fail/unknown"
  fi
}

# --- runner ------------------------------------------------------------------

CASES=(
  case_inline_executes_directly
  case_durable_stops_before_source_edit
  case_approved_durable_reports_evidence
)

main() {
  log "model: $EVAL_MODEL"
  log "sandboxes: $RUN_ROOT"
  log ""

  if [[ $# -gt 0 ]]; then
    "$@"
  else
    for case_name in "${CASES[@]}"; do
      "$case_name"
      log ""
    done
  fi

  if (( FAILURES > 0 )); then
    log "$FAILURES assertion(s) failed. Sandboxes kept at $RUN_ROOT"
    exit 1
  fi
  log "All assertions passed. Sandboxes kept at $RUN_ROOT"
}

main "$@"
