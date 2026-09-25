#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_SCRIPT="$REPO_ROOT/scripts/install.sh"
UNINSTALL_SCRIPT="$REPO_ROOT/scripts/uninstall.sh"

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

assert_absent() {
  [[ ! -e "$1" && ! -L "$1" ]] || fail "expected $1 to be absent"
}

run_install() {
  local fake_home="$1"
  shift

  HOME="$fake_home" bash "$INSTALL_SCRIPT" --home "$fake_home" --skip-external "$@"
}

fresh_install_creates_expected_links() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  local fake_home="$temp_dir/home"

  run_install "$fake_home" >/dev/null

  local skill_dir
  for skill_dir in "$REPO_ROOT"/skills/*/; do
    local name
    name="$(basename "$skill_dir")"
    assert_symlink_target "$fake_home/.agents/skills/$name" "$REPO_ROOT/skills/$name"
  done
  assert_symlink_target "$fake_home/.pi/agent/rules" "$REPO_ROOT/rules"
  [[ -f "$fake_home/.pi/agent/AGENTS.md" ]] || fail "expected generated pi instructions"
  grep -q '~/.pi/agent/rules/' "$fake_home/.pi/agent/AGENTS.md" || fail "expected pi instructions to point to the rules"
  assert_absent "$fake_home/.claude"
  assert_absent "$fake_home/.codex"
  assert_absent "$fake_home/.gemini"

  rm -rf "$temp_dir"
}

install_is_idempotent_and_writes_pi_settings() {
  python3 - "$INSTALL_SCRIPT" <<'PY'
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

install = sys.argv[1]


def run(home, *args):
    env = {**os.environ, "HOME": str(home)}
    subprocess.run(["bash", install, "--home", str(home), "--skip-external", *args], env=env, check=True, stdout=subprocess.DEVNULL)


def snapshot(home):
    return {str(path.relative_to(home)): (os.readlink(path) if path.is_symlink() else hashlib.sha256(path.read_bytes()).hexdigest())
            for path in home.rglob("*") if path.is_symlink() or path.is_file()}


with tempfile.TemporaryDirectory() as directory:
    home = Path(directory)
    run(home)
    first = snapshot(home)
    run(home)
    assert snapshot(home) == first
    text = (home / ".pi/agent/AGENTS.md").read_text()
    assert all(word not in text for word in ("@shared/", "boss-say", "straw-boss", "/codex:rescue"))
    settings = json.loads((home / ".pi/agent/settings.json").read_text())
    assert len(settings["packages"]) == 15, settings
    assert settings["packages"][0] == "git:github.com/wayne930242/pi-claude-bridge@31891e9395e510f583def3bd0e01a663582d59a4", settings
    assert settings["defaultProvider"] == "claude-bridge", settings
    assert settings["theme"] == "catppuccin-mocha", settings
    assert settings["editorPaddingX"] == 1, settings
    assert settings["collapseChangelog"] is True, settings
    assert settings["terminal"]["showTerminalProgress"] is True, settings
    assert "powerline" not in settings and "npm:pi-open-tui" in settings["packages"], settings
    mcp = json.loads((home / ".pi/agent/mcp.json").read_text())
    assert mcp["settings"]["hostConfigDiscovery"] == "on", mcp
    config = json.loads((home / ".pi/agent/herdr-agents/config.json").read_text())
    assert config["status"] == {"enabled": True}, config
    assert config["panes"] == {"mode": "split", "direction": "right"}, config
PY
}

target_option_is_rejected() {
  local temp_dir
  temp_dir="$(mktemp -d)"

  if run_install "$temp_dir/home" --target pi >/dev/null 2>&1; then
    fail "expected --target to be rejected"
  fi

  rm -rf "$temp_dir"
}

conflict_without_force_fails() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.pi/agent/rules"
  printf 'mine\n' > "$fake_home/.pi/agent/rules/own.md"

  if run_install "$fake_home" >/dev/null 2>&1; then
    fail "expected install to fail when ~/.pi/agent/rules already exists without --force"
  fi

  rm -rf "$temp_dir"
}

force_replaces_and_backs_up_conflicts() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  local fake_home="$temp_dir/home"
  mkdir -p "$fake_home/.pi/agent/rules"
  printf 'mine\n' > "$fake_home/.pi/agent/rules/own.md"
  printf 'user instructions\n' > "$fake_home/.pi/agent/AGENTS.md"

  run_install "$fake_home" --force >/dev/null

  assert_symlink_target "$fake_home/.pi/agent/rules" "$REPO_ROOT/rules"
  local backup_base="$fake_home/.local/state/weihung-user-claude/backups"
  local backup_file
  backup_file="$(find "$backup_base" -type f -path '*/.pi/agent/rules/own.md' | head -n 1)"
  [[ -n "$backup_file" && "$(cat "$backup_file")" == "mine" ]] || fail "expected backed up rules directory"
  backup_file="$(find "$backup_base" -type f -path '*/.pi/agent/AGENTS.md' | head -n 1)"
  [[ -n "$backup_file" && "$(cat "$backup_file")" == "user instructions" ]] || fail "expected backed up pi instructions"

  rm -rf "$temp_dir"
}

install_prunes_retired_links_and_retires_skill_copies() {
  local temp_dir
  temp_dir="$(mktemp -d)"
  local fake_home="$temp_dir/home"
  local user_skill="$temp_dir/my-custom-skill"
  mkdir -p "$fake_home/.agents/skills/providing-knowledge" "$user_skill"
  printf 'stale copy\n' > "$fake_home/.agents/skills/providing-knowledge/SKILL.md"
  ln -s "$REPO_ROOT/skills/leveraging-tasks" "$fake_home/.agents/skills/leveraging-tasks"
  ln -s "$user_skill" "$fake_home/.agents/skills/my-custom-skill"

  run_install "$fake_home" >/dev/null

  assert_absent "$fake_home/.agents/skills/leveraging-tasks"
  assert_symlink_target "$fake_home/.agents/skills/my-custom-skill" "$user_skill"
  assert_symlink_target "$fake_home/.agents/skills/providing-knowledge" "$REPO_ROOT/skills/providing-knowledge"
  [[ -n "$(find "$fake_home/.local/state/weihung-user-claude/backups" -path '*/providing-knowledge/SKILL.md')" ]] \
    || fail "expected the stale skill copy in the backup"

  rm -rf "$temp_dir"
}

install_preserves_user_pi_state() {
  python3 - "$INSTALL_SCRIPT" "$UNINSTALL_SCRIPT" <<'PY'
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

install, uninstall = sys.argv[1:]


def run(script, home, *args):
    env = {**os.environ, "HOME": str(home)}
    subprocess.run(["bash", script, "--home", str(home), "--skip-external", *args], env=env, check=True, stdout=subprocess.DEVNULL)


with tempfile.TemporaryDirectory() as directory:
    home = Path(directory)
    agent = home / ".pi/agent"
    agent.mkdir(parents=True)
    (agent / "AGENTS.md").write_text("user instructions\n")
    (agent / "settings.json").write_text(json.dumps({"packages": ["npm:pi-claude-bridge", "npm:user-package"], "theme": "light", "terminal": {"showImages": False}, "powerline": {"welcome": False}}))
    config = agent / "herdr-agents/config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    original_models = {"default": "user/model", "agents": {"scout": "user/scout"}}
    config.write_text(json.dumps({"models": original_models, "panes": {"mode": "tab"}, "other": True}))
    run(install, home, "--force")
    installed_packages = json.loads((agent / "settings.json").read_text())["packages"]
    assert "npm:pi-claude-bridge" not in installed_packages, installed_packages
    assert any(package.startswith("git:github.com/wayne930242/pi-claude-bridge@31891e9") for package in installed_packages), installed_packages
    assert json.loads(config.read_text())["models"]["agents"] == original_models["agents"]
    subprocess.run(["python3", str(Path(install).with_name("pi-target.py")), "apply-profile", "--home", str(home)], check=True)
    run(uninstall, home)
    assert (agent / "AGENTS.md").read_text() == "user instructions\n"
    settings = json.loads((agent / "settings.json").read_text())
    assert settings["packages"] == ["npm:pi-claude-bridge", "npm:user-package"], settings
    assert settings["theme"] == "light", settings
    assert settings["terminal"] == {"showImages": False}, settings
    assert settings["powerline"] == {"welcome": False}, settings
    assert json.loads(config.read_text()) == {"models": original_models, "panes": {"mode": "tab"}, "other": True}
PY
}

apply_profile_follows_the_active_strategy() {
  python3 - "$REPO_ROOT" <<'PY'
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

source = Path(sys.argv[1])
with tempfile.TemporaryDirectory() as directory:
    temporary = Path(directory)
    clone = temporary / "repo"
    for relative in ("pi/AGENTS.md.in", "pi/model-profiles.json", "scripts/pi-target.py",
                     "skills/managing-model-preferences/model-preference-profile.md"):
        destination = clone / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / relative, destination)
    home = temporary / "home"
    script = clone / "scripts/pi-target.py"
    subprocess.run(["python3", str(script), "install", "--home", str(home), "--skip-external"], check=True)
    profile = clone / "skills/managing-model-preferences/model-preference-profile.md"
    profile.write_text(profile.read_text().replace(
        "Active strategy: [claude-drive-codex](strategies/claude-drive-codex.md).",
        "Active strategy: [codex-first](strategies/codex-first.md).",
    ))
    subprocess.run(["python3", str(script), "apply-profile", "--home", str(home)], check=True)
    settings = json.loads((home / ".pi/agent/settings.json").read_text())
    assert (settings["defaultProvider"], settings["defaultModel"]) == ("openai-codex", "gpt-6-sol")
    config = json.loads((home / ".pi/agent/herdr-agents/config.json").read_text())
    assert config["models"]["tasks"]["recon"][0] == "openai-codex/gpt-6-luna"
    assert "Active model strategy: codex-first" in (home / ".pi/agent/AGENTS.md").read_text()
PY
}

run_all_tests() {
  fresh_install_creates_expected_links
  install_is_idempotent_and_writes_pi_settings
  target_option_is_rejected
  conflict_without_force_fails
  force_replaces_and_backs_up_conflicts
  install_prunes_retired_links_and_retires_skill_copies
  install_preserves_user_pi_state
  apply_profile_follows_the_active_strategy
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
  printf 'install: pass\n'
else
  "$1"
fi
