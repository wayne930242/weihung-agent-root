#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_SCRIPT="$REPO_ROOT/scripts/install.sh"
UNINSTALL_SCRIPT="$REPO_ROOT/scripts/uninstall.sh"

fail() {
  printf 'FAIL: %s\n' "$*" >&2
  exit 1
}

run_install() {
  local fake_home="$1"
  shift

  HOME="$fake_home" bash "$INSTALL_SCRIPT" --home "$fake_home" "$@"
}

run_uninstall() {
  local fake_home="$1"
  shift

  HOME="$fake_home" bash "$UNINSTALL_SCRIPT" --home "$fake_home" "$@"
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

restore_from_backup_and_clean_hooks() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude" "$fake_home/.codex/rules"
  printf 'old claude\n' > "$fake_home/.claude/CLAUDE.md"
  printf 'old codex agents\n' > "$fake_home/.codex/AGENTS.md"
  printf 'old rule\n' > "$fake_home/.codex/rules/default.rules"
  cat > "$fake_home/.claude/settings.json" <<'EOF'
{
  "customSetting": true,
  "effortLevel": "xhigh"
}
EOF

  run_install "$fake_home" --force
  run_uninstall "$fake_home"

  [[ "$(cat "$fake_home/.claude/CLAUDE.md")" == "old claude" ]] || fail "expected CLAUDE.md to be restored from backup"
  [[ "$(cat "$fake_home/.codex/AGENTS.md")" == "old codex agents" ]] || fail "expected AGENTS.md to be restored from backup"
  [[ "$(cat "$fake_home/.codex/rules/default.rules")" == "old rule" ]] || fail "expected default.rules to be restored from backup"
  [[ ! -e "$fake_home/.claude/shared/communication.md" ]] || fail "expected managed shared file to be removed"
  [[ ! -e "$fake_home/.codex/skills/leveraging-tasks" ]] || fail "expected managed codex skill to be removed"
  [[ ! -e "$fake_home/.codex/agents/docs-researcher.toml" ]] || fail "expected managed codex agent to be removed"
  [[ ! -e "$fake_home/.codex/agents/article-writer.toml" ]] || fail "expected managed article writer to be removed"
  [[ ! -e "$fake_home/.codex/hooks.json" ]] || fail "expected managed codex hooks.json to be removed"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert settings["customSetting"] is True, settings
assert settings["effortLevel"] == "xhigh", settings
assert "hooks" not in settings, settings
assert "model" not in settings, settings
assert "advisorModel" not in settings, settings
assert "env" not in settings, settings
PY

  rm -rf "$temp_dir"
}

uninstall_removes_only_repository_managed_retired_safety_reviewer() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.codex/agents"
  ln -s "$REPO_ROOT/codex/agents/safety-reviewer.toml" "$fake_home/.codex/agents/safety-reviewer.toml"

  run_uninstall "$fake_home"

  [[ ! -e "$fake_home/.codex/agents/safety-reviewer.toml" && ! -L "$fake_home/.codex/agents/safety-reviewer.toml" ]] || fail "expected retired repository safety reviewer to be removed"

  rm -rf "$temp_dir"
}

uninstall_preserves_user_owned_safety_reviewer() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  local user_agent="$temp_dir/user-safety-reviewer.toml"
  mkdir -p "$fake_home/.codex/agents"
  printf 'name = "user_safety_reviewer"\n' > "$user_agent"
  ln -s "$user_agent" "$fake_home/.codex/agents/safety-reviewer.toml"

  run_uninstall "$fake_home"

  [[ -L "$fake_home/.codex/agents/safety-reviewer.toml" ]] || fail "expected user-owned safety reviewer to survive uninstall"
  [[ "$(readlink "$fake_home/.codex/agents/safety-reviewer.toml")" == "$user_agent" ]] || fail "expected user-owned safety reviewer target to survive uninstall"

  rm -rf "$temp_dir"
}

fresh_install_uninstall_removes_managed_files() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home"

  run_install "$fake_home"
  run_uninstall "$fake_home"

  [[ ! -e "$fake_home/.claude/CLAUDE.md" ]] || fail "expected CLAUDE.md to be removed when no backup exists"
  [[ ! -e "$fake_home/.codex/AGENTS.md" ]] || fail "expected AGENTS.md to be removed when no backup exists"
  [[ ! -e "$fake_home/.codex/skills/leveraging-tasks" ]] || fail "expected codex skill to be removed when no backup exists"
  [[ ! -e "$fake_home/.claude/skills/leveraging-tasks" ]] || fail "expected claude skill to be removed when no backup exists"
  [[ ! -e "$fake_home/.codex/rules/default.rules" ]] || fail "expected default.rules to be removed when no backup exists"

  python3 - <<PY
import json
from pathlib import Path
settings_path = Path("$fake_home/.claude/settings.json")
if settings_path.exists():
    settings = json.loads(settings_path.read_text())
    assert "hooks" not in settings, settings
PY

  rm -rf "$temp_dir"
}

latest_backup_directory_wins() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  local backup_base="$fake_home/.local/state/weihung-user-claude/backups"
  mkdir -p "$fake_home/.claude" "$backup_base/20250101-000000/.claude" "$backup_base/20250102-000000/.claude"

  ln -s "$REPO_ROOT/CLAUDE.md" "$fake_home/.claude/CLAUDE.md"
  printf 'older backup\n' > "$backup_base/20250101-000000/.claude/CLAUDE.md"
  printf 'newer backup\n' > "$backup_base/20250102-000000/.claude/CLAUDE.md"

  run_uninstall "$fake_home"

  [[ "$(cat "$fake_home/.claude/CLAUDE.md")" == "newer backup" ]] || fail "expected uninstall to restore from the latest backup directory"

  rm -rf "$temp_dir"
}

uninstall_keeps_user_model_preferences() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home"

  run_install "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings_path = Path("$fake_home/.claude/settings.json")
settings = json.loads(settings_path.read_text())
settings["model"] = "user-main-model"
settings["advisorModel"] = "user-advisor-model"
settings["env"] = {"CLAUDE_CODE_SUBAGENT_MODEL": "user-worker-model"}
settings_path.write_text(json.dumps(settings, indent=2) + "\n")
PY

  run_uninstall "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert settings["model"] == "user-main-model", settings
assert settings["advisorModel"] == "user-advisor-model", settings
assert settings["env"]["CLAUDE_CODE_SUBAGENT_MODEL"] == "user-worker-model", settings
PY

  rm -rf "$temp_dir"
}


aborted_uninstall_never_leaves_missing_hooks_registered() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.claude/shared"
  printf 'old shared\n' > "$fake_home/.claude/shared/communication.md"

  run_install "$fake_home" --force

  rm "$fake_home/.claude/shared/communication.md"
  printf 'user replaced this\n' > "$fake_home/.claude/shared/communication.md"

  if run_uninstall "$fake_home"; then
    fail "expected uninstall to fail when a managed file was replaced by a real file"
  fi

  assert_registered_hooks_runnable "$fake_home"

  rm -rf "$temp_dir"
}

uninstall_drops_registration_left_by_an_older_fragment() {
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
            "command": "\"$HOME/.claude/hooks/log-notification.sh\"",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
EOF

  run_install "$fake_home"

  [[ -x "$fake_home/.claude/hooks/log-notification.sh" ]] || fail "expected install to link log-notification.sh"

  run_uninstall "$fake_home"

  [[ ! -e "$fake_home/.claude/hooks/log-notification.sh" ]] || fail "expected uninstall to remove log-notification.sh"

  assert_registered_hooks_runnable "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings_path = Path("$fake_home/.claude/settings.json")
if settings_path.exists():
    settings = json.loads(settings_path.read_text())
    assert "hooks" not in settings, settings
PY

  rm -rf "$temp_dir"
}

uninstall_keeps_unmanaged_hook_registrations() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home"

  run_install "$fake_home"

  mkdir -p "$fake_home/.claude/hooks"
  printf '#!/usr/bin/env bash\nexit 0\n' > "$fake_home/.claude/hooks/third-party.sh"
  chmod +x "$fake_home/.claude/hooks/third-party.sh"

  python3 - <<PY
import json
from pathlib import Path
settings_path = Path("$fake_home/.claude/settings.json")
settings = json.loads(settings_path.read_text())
settings["hooks"]["SessionStart"] = [
    {
        "matcher": "*",
        "hooks": [
            {"type": "command", "command": '"\$HOME/.claude/hooks/third-party.sh"', "timeout": 10}
        ],
    }
]
settings_path.write_text(json.dumps(settings, indent=2) + "\n")
PY

  run_uninstall "$fake_home"

  python3 - <<PY
import json
from pathlib import Path
settings = json.loads(Path("$fake_home/.claude/settings.json").read_text())
assert "Stop" not in settings.get("hooks", {}), settings
entry = settings["hooks"]["SessionStart"][0]
assert entry["hooks"][0]["command"] == '"\$HOME/.claude/hooks/third-party.sh"', settings
PY

  rm -rf "$temp_dir"
}

run_all_tests() {
  restore_from_backup_and_clean_hooks
  aborted_uninstall_never_leaves_missing_hooks_registered
  uninstall_drops_registration_left_by_an_older_fragment
  uninstall_keeps_unmanaged_hook_registrations
  fresh_install_uninstall_removes_managed_files
  latest_backup_directory_wins
  uninstall_keeps_user_model_preferences
  uninstall_removes_only_repository_managed_retired_safety_reviewer
  uninstall_preserves_user_owned_safety_reviewer
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
else
  "$1"
fi
