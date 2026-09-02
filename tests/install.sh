#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_SCRIPT="$REPO_ROOT/scripts/install.sh"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

assert_symlink_target() {
  local path="$1"
  local expected="$2"

  [[ -L "$path" ]] || fail "expected symlink at $path"
  local actual
  actual="$(readlink "$path")"
  [[ "$actual" == "$expected" ]] || fail "expected $path -> $expected, got $actual"
}

run_install() {
  local fake_home="$1"
  shift

  HOME="$fake_home" bash "$INSTALL_SCRIPT" --home "$fake_home" "$@"
}

assert_registered_hooks_runnable() {
  local fake_home="$1"

  python3 - "$fake_home" <<'PY'
import json
import os
import sys
from pathlib import Path

fake_home = sys.argv[1]
settings_path = Path(fake_home) / ".claude/settings.json"
if not settings_path.exists():
    raise SystemExit(0)

settings = json.loads(settings_path.read_text(encoding="utf-8"))
missing = []
for entries in settings.get("hooks", {}).values():
    for entry in entries:
        for hook in entry.get("hooks", []):
            command = hook.get("command", "").strip('"')
            if not command.startswith("$HOME/"):
                continue
            script = command.replace("$HOME", fake_home, 1)
            if not os.access(script, os.X_OK):
                missing.append(script)

if missing:
    raise SystemExit("settings.json registers unrunnable hook commands: %s" % missing)
PY
}

fresh_install_creates_expected_symlinks() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home"

  run_install "$fake_home"

  assert_symlink_target "$fake_home/.claude/CLAUDE.md" "$REPO_ROOT/CLAUDE.md"
  assert_symlink_target "$fake_home/.codex/AGENTS.md" "$REPO_ROOT/AGENTS.md"
  assert_symlink_target "$fake_home/.claude/shared/communication.md" "$REPO_ROOT/shared/communication.md"
  assert_symlink_target "$fake_home/.claude/shared/engineering.md" "$REPO_ROOT/shared/engineering.md"
  assert_symlink_target "$fake_home/.claude/shared/context-management.md" "$REPO_ROOT/shared/context-management.md"
  assert_symlink_target "$fake_home/.claude/hooks/log-notification.sh" "$REPO_ROOT/claude/hooks/log-notification.sh"
  assert_symlink_target "$fake_home/.claude/hooks/log-stop.sh" "$REPO_ROOT/claude/hooks/log-stop.sh"
  assert_symlink_target "$fake_home/.claude/agents/security-reviewer.md" "$REPO_ROOT/claude/agents/security-reviewer.md"
  assert_symlink_target "$fake_home/.claude/agents/silent-failure-hunter.md" "$REPO_ROOT/claude/agents/silent-failure-hunter.md"
  assert_symlink_target "$fake_home/.codex/skills/assuring-quality" "$REPO_ROOT/skills/assuring-quality"
  assert_symlink_target "$fake_home/.codex/skills/inspecting" "$REPO_ROOT/skills/inspecting"
  assert_symlink_target "$fake_home/.codex/skills/investigating" "$REPO_ROOT/skills/investigating"
  assert_symlink_target "$fake_home/.codex/skills/leveraging-tasks" "$REPO_ROOT/skills/leveraging-tasks"
  [[ ! -e "$fake_home/.claude/skills/tdd" && ! -L "$fake_home/.claude/skills/tdd" ]] || fail "did not expect retired tdd skill in Claude root"
  [[ ! -e "$fake_home/.codex/skills/tdd" && ! -L "$fake_home/.codex/skills/tdd" ]] || fail "did not expect retired tdd skill in Codex root"
  assert_symlink_target "$fake_home/.codex/skills/codebase-design" "$REPO_ROOT/skills/codebase-design"
  assert_symlink_target "$fake_home/.codex/skills/domain-modeling" "$REPO_ROOT/skills/domain-modeling"
  assert_symlink_target "$fake_home/.codex/skills/prototype" "$REPO_ROOT/skills/prototype"
  assert_symlink_target "$fake_home/.codex/skills/providing-knowledge" "$REPO_ROOT/skills/providing-knowledge"
  assert_symlink_target "$fake_home/.codex/skills/reflecting-to-root" "$REPO_ROOT/skills/reflecting-to-root"
  assert_symlink_target "$fake_home/.codex/agents/docs-researcher.toml" "$REPO_ROOT/codex/agents/docs-researcher.toml"
  assert_symlink_target "$fake_home/.codex/agents/article-writer.toml" "$REPO_ROOT/codex/agents/article-writer.toml"
  [[ ! -e "$fake_home/.codex/agents/safety-reviewer.toml" && ! -L "$fake_home/.codex/agents/safety-reviewer.toml" ]] || fail "did not expect retired safety reviewer"
  assert_symlink_target "$fake_home/.codex/rules/default.rules" "$REPO_ROOT/codex/rules/default.rules"
  assert_symlink_target "$fake_home/.codex/hooks/log-session-start.sh" "$REPO_ROOT/codex/hooks/log-session-start.sh"
  assert_symlink_target "$fake_home/.codex/hooks/log-stop.sh" "$REPO_ROOT/codex/hooks/log-stop.sh"
  assert_symlink_target "$fake_home/.codex/hooks.json" "$REPO_ROOT/codex/hooks.json"

  python3 - <<PY
from pathlib import Path

expected_models = {
    "docs-researcher.toml": "gpt-5.6-luna",
    "article-writer.toml": "gpt-5.6-sol",
}
for name, expected_model in expected_models.items():
    lines = (
        Path("$fake_home") / ".codex/agents" / name
    ).read_text(encoding="utf-8").splitlines()
    assert f'model = "{expected_model}"' in lines, (name, lines)
PY

  rg -Fq 'Writing or substantially rewriting an article' "$fake_home/.claude/CLAUDE.md"
  rg -Fq -- '--model gpt-5.6-sol' "$fake_home/.claude/CLAUDE.md"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert "hooks" in settings, settings
assert "Stop" in settings["hooks"], settings
assert "Notification" not in settings["hooks"], settings
assert settings["crossSessionInbound"] == "accept", settings
assert settings["model"] == "claude-fable-5-1", settings
assert "advisorModel" not in settings, settings
PY

  [[ ! -e "$fake_home/.codex/config.toml" ]] || fail "did not expect installer to rewrite ~/.codex/config.toml in the light layout"

  rm -rf "$temp_dir"
}

conflict_without_force_fails() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude"
  printf 'existing\n' > "$fake_home/.claude/CLAUDE.md"

  if run_install "$fake_home"; then
    fail "expected install to fail when CLAUDE.md already exists without --force"
  fi

  rm -rf "$temp_dir"
}

force_replaces_and_backs_up_conflicts() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude"
  printf 'existing\n' > "$fake_home/.claude/CLAUDE.md"

  run_install "$fake_home" --force

  assert_symlink_target "$fake_home/.claude/CLAUDE.md" "$REPO_ROOT/CLAUDE.md"

  local backup_base="$fake_home/.local/state/weihung-user-claude/backups"
  [[ -d "$backup_base" ]] || fail "expected backup directory at $backup_base"

  local backup_file
  backup_file="$(find "$backup_base" -type f -path '*/.claude/CLAUDE.md' | head -n 1)"
  [[ -n "$backup_file" ]] || fail "expected backed up CLAUDE.md"
  [[ "$(cat "$backup_file")" == "existing" ]] || fail "expected backup to preserve previous content"

  rm -rf "$temp_dir"
}

existing_settings_are_merged_not_replaced() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude"
  cat > "$fake_home/.claude/settings.json" <<'EOF'
{
  "customSetting": true,
  "effortLevel": "xhigh"
}
EOF

  run_install "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert settings["customSetting"] is True, settings
assert settings["effortLevel"] == "xhigh", settings
assert "Stop" in settings["hooks"], settings
assert "Notification" not in settings["hooks"], settings
assert settings["crossSessionInbound"] == "accept", settings
PY

  rm -rf "$temp_dir"
}

fresh_install_manages_explicit_model_settings() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home"

  run_install "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert settings["model"] == "claude-fable-5-1", settings
assert "advisorModel" not in settings, settings
assert "env" not in settings, settings
assert settings["crossSessionInbound"] == "accept", settings
assert "Stop" in settings["hooks"], settings
assert "statusLine" in settings, settings
PY

  rm -rf "$temp_dir"
}

former_managed_opus_advisor_is_removed_on_upgrade() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude"
  cat > "$fake_home/.claude/settings.json" <<'EOF'
{
  "model": "sonnet",
  "advisorModel": "opus",
  "customSetting": true
}
EOF

  run_install "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert settings["model"] == "claude-fable-5-1", settings
assert "advisorModel" not in settings, settings
assert settings["customSetting"] is True, settings
PY

  rm -rf "$temp_dir"
}

user_selected_advisor_survives_install() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude"
  cat > "$fake_home/.claude/settings.json" <<'EOF'
{
  "advisorModel": "user-advisor-model"
}
EOF

  run_install "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert settings["model"] == "claude-fable-5-1", settings
assert settings["advisorModel"] == "user-advisor-model", settings
PY

  rm -rf "$temp_dir"
}

legacy_worker_pin_is_replaced_by_fable_main() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude"
  cat > "$fake_home/.claude/settings.json" <<'EOF'
{
  "model": "user-main-model",
  "advisorModel": "user-advisor-model",
  "env": {
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet",
    "USER_ENV": "keep-me"
  }
}
EOF

  run_install "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert settings["model"] == "claude-fable-5-1", settings
assert settings["advisorModel"] == "user-advisor-model", settings
assert "CLAUDE_CODE_SUBAGENT_MODEL" not in settings["env"], settings
assert settings["env"]["USER_ENV"] == "keep-me", settings
PY

  rm -rf "$temp_dir"
}

legacy_only_worker_pin_removes_empty_env() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude"
  cat > "$fake_home/.claude/settings.json" <<'EOF'
{
  "env": {
    "CLAUDE_CODE_SUBAGENT_MODEL": "sonnet"
  }
}
EOF

  run_install "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert "env" not in settings, settings
assert settings["model"] == "claude-fable-5-1", settings
assert "advisorModel" not in settings, settings
PY

  rm -rf "$temp_dir"
}

user_selected_worker_model_survives_install() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude"
  cat > "$fake_home/.claude/settings.json" <<'EOF'
{
  "env": {
    "CLAUDE_CODE_SUBAGENT_MODEL": "user-worker-model"
  }
}
EOF

  run_install "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert settings["env"]["CLAUDE_CODE_SUBAGENT_MODEL"] == "user-worker-model", settings
assert settings["model"] == "claude-fable-5-1", settings
assert "advisorModel" not in settings, settings
PY

  rm -rf "$temp_dir"
}

non_object_env_does_not_break_install() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude"
  cat > "$fake_home/.claude/settings.json" <<'EOF'
{
  "env": "user-value"
}
EOF

  run_install "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert settings["env"] == "user-value", settings
assert settings["model"] == "claude-fable-5-1", settings
assert "advisorModel" not in settings, settings
PY

  rm -rf "$temp_dir"
}

install_removes_only_repository_managed_retired_safety_reviewer() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.codex/agents"
  ln -s "$REPO_ROOT/codex/agents/safety-reviewer.toml" "$fake_home/.codex/agents/safety-reviewer.toml"

  run_install "$fake_home"

  [[ ! -e "$fake_home/.codex/agents/safety-reviewer.toml" && ! -L "$fake_home/.codex/agents/safety-reviewer.toml" ]] || fail "expected retired repository safety reviewer to be removed"

  rm -rf "$temp_dir"
}

install_preserves_user_owned_safety_reviewer() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  local user_agent="$temp_dir/user-safety-reviewer.toml"
  mkdir -p "$fake_home/.codex/agents"
  printf 'name = "user_safety_reviewer"\n' > "$user_agent"
  ln -s "$user_agent" "$fake_home/.codex/agents/safety-reviewer.toml"

  run_install "$fake_home"

  assert_symlink_target "$fake_home/.codex/agents/safety-reviewer.toml" "$user_agent"

  rm -rf "$temp_dir"
}

install_removes_only_repository_managed_retired_tdd_skills() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude/skills" "$fake_home/.codex/skills"
  ln -s "$REPO_ROOT/skills/tdd" "$fake_home/.claude/skills/tdd"
  ln -s "$REPO_ROOT/skills/tdd" "$fake_home/.codex/skills/tdd"

  run_install "$fake_home"

  [[ ! -e "$fake_home/.claude/skills/tdd" && ! -L "$fake_home/.claude/skills/tdd" ]] || fail "expected retired Claude tdd skill to be removed"
  [[ ! -e "$fake_home/.codex/skills/tdd" && ! -L "$fake_home/.codex/skills/tdd" ]] || fail "expected retired Codex tdd skill to be removed"

  rm -rf "$temp_dir"
}

install_preserves_user_owned_tdd_skills() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  local user_skill="$temp_dir/user-tdd"
  mkdir -p "$fake_home/.claude/skills" "$fake_home/.codex/skills" "$user_skill"
  ln -s "$user_skill" "$fake_home/.claude/skills/tdd"
  ln -s "$user_skill" "$fake_home/.codex/skills/tdd"

  run_install "$fake_home"

  assert_symlink_target "$fake_home/.claude/skills/tdd" "$user_skill"
  assert_symlink_target "$fake_home/.codex/skills/tdd" "$user_skill"

  rm -rf "$temp_dir"
}


aborted_install_never_registers_missing_hooks() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude/agents"
  printf 'existing\n' > "$fake_home/.claude/agents/security-reviewer.md"

  if run_install "$fake_home"; then
    fail "expected install to fail when a managed agent already exists without --force"
  fi

  assert_registered_hooks_runnable "$fake_home"

  rm -rf "$temp_dir"
}

install_drops_registration_left_by_an_older_fragment() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude"
  cat > "$fake_home/.claude/settings.json" <<'EOF'
{
  "hooks": {
    "Notification": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "\"$HOME/.claude/hooks/log-legacy.sh\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
EOF

  run_install "$fake_home"

  assert_registered_hooks_runnable "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert "Notification" not in settings["hooks"], settings
assert "Stop" in settings["hooks"], settings
PY

  rm -rf "$temp_dir"
}

install_keeps_unmanaged_hook_registrations() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude/hooks"
  printf '#!/usr/bin/env bash\nexit 0\n' > "$fake_home/.claude/hooks/third-party.sh"
  chmod +x "$fake_home/.claude/hooks/third-party.sh"
  cat > "$fake_home/.claude/settings.json" <<'EOF'
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "\"$HOME/.claude/hooks/third-party.sh\"",
            "timeout": 10
          }
        ]
      }
    ]
  }
}
EOF

  run_install "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
entry = settings["hooks"]["SessionStart"][0]
assert entry["matcher"] == "*", settings
assert entry["hooks"][0]["command"] == '"\$HOME/.claude/hooks/third-party.sh"', settings
PY

  rm -rf "$temp_dir"
}

run_all_tests() {
  fresh_install_creates_expected_symlinks
  aborted_install_never_registers_missing_hooks
  install_drops_registration_left_by_an_older_fragment
  install_keeps_unmanaged_hook_registrations
  conflict_without_force_fails
  force_replaces_and_backs_up_conflicts
  existing_settings_are_merged_not_replaced
  fresh_install_manages_explicit_model_settings
  former_managed_opus_advisor_is_removed_on_upgrade
  user_selected_advisor_survives_install
  legacy_worker_pin_is_replaced_by_fable_main
  legacy_only_worker_pin_removes_empty_env
  user_selected_worker_model_survives_install
  non_object_env_does_not_break_install
  install_removes_only_repository_managed_retired_safety_reviewer
  install_preserves_user_owned_safety_reviewer
  install_removes_only_repository_managed_retired_tdd_skills
  install_preserves_user_owned_tdd_skills
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
else
  "$1"
fi
