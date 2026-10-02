#!/usr/bin/env bash

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_SCRIPT="$REPO_ROOT/scripts/install.sh"
UNINSTALL_SCRIPT="$REPO_ROOT/scripts/uninstall.sh"
export PI_SDLC_ROOT="$REPO_ROOT/.no-sdlc-checkout" PI_MP_INFRA_ROOT="$REPO_ROOT/.no-mp-infra-checkout"

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
  assert_symlink_target "$fake_home/.pi/agent/agents" "$REPO_ROOT/agents"
  [[ -f "$fake_home/.pi/agent/AGENTS.md" ]] || fail "expected generated pi instructions"
  # The literal tilde is the text the generated instructions contain, not a path to expand.
  # shellcheck disable=SC2088
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
    assert all(word not in text for word in ("@shared/", "/codex:rescue"))
    assert "Straw Boss `boss-say`" in text and "dispatch_control" in text
    assert "## Memory" in text and "memory_write" in text and "memory_search" in text, text
    settings = json.loads((home / ".pi/agent/settings.json").read_text())
    assert len(settings["packages"]) == 25, settings
    assert settings["packages"][0] == "git:github.com/wayne930242/pi-claude-bridge@b2735123eb51862136667b5f829ce1343bb7f93b", settings
    sources = [package["source"] if isinstance(package, dict) else package for package in settings["packages"]]
    registry = [source.removeprefix("npm:") for source in sources if source.startswith("npm:")]
    assert registry and all("@" in name[1:] for name in registry), registry
    assert {"source": "npm:@victor-software-house/pi-curated-themes@0.2.1", "themes": ["themes/catppuccin-mocha.json"], "skills": []} in settings["packages"], settings
    assert "npm:@juicesharp/rpiv-todo@2.12.0" in sources and "npm:cc-safety-net@2.5.0" in sources, sources
    assert "npm:pi-codex-image-gen@0.1.13" in sources and "npm:pi-web-access@0.35.0" in sources, sources
    assert "npm:pi-secret-drop@0.1.6" in sources and "npm:pi-robot-hand@0.1.1" in sources, sources
    assert "npm:pi-phoenix-otel@0.2.0" in sources, sources
    assert "npm:@pify/memory@0.13.1" in sources, sources
    assert "npm:pi-loop-monitor@0.2.1" in sources, sources
    assert "npm:@narumitw/pi-goal@0.54.8" in sources, sources
    assert {"source": "npm:pi-code@1.4.1", "extensions": ["extensions/claude-rules.ts"]} in settings["packages"], settings
    assert not any("pi-todo" in source or "catppuccin" in source for source in sources), sources
    assert not {"defaultProvider", "defaultModel", "defaultThinkingLevel", "enabledModels"} & set(settings), settings
    assert settings["theme"] == "catppuccin-mocha", settings
    assert settings["enableInstallTelemetry"] is False, settings
    assert settings["editorPaddingX"] == 1, settings
    assert settings["collapseChangelog"] is True, settings
    assert settings["terminal"]["showTerminalProgress"] is True, settings
    assert settings["compaction"] == {"modelOverrides": {"claude-bridge/claude-opus-5-5": {"reserveTokens": 500000}, "claude-bridge/claude-sonnet-5-5": {"reserveTokens": 500000}}}, settings
    assert "powerline" not in settings and "npm:pi-open-tui@0.3.10" in settings["packages"], settings
    mcp = json.loads((home / ".pi/agent/mcp-adapter.json").read_text())
    assert mcp["settings"] == {"hostConfigDiscovery": "on", "namespaceProxyTools": False}, mcp
    assert mcp["mcpServers"]["codebase-memory-mcp"] == {"disabled": True}, mcp
    assert mcp["mcpServers"]["research-hub"]["args"] == ["-y", "thesis-toolkit@0.1.2", "mcp", "research-hub"], mcp
    assert set(mcp["mcpServers"]) == {"codebase-memory-mcp", "research-hub"}, mcp
    lens = json.loads((home / ".pi-lens/config.json").read_text())
    assert lens == {"tools": {name: {"enabled": False} for name in ("project_report", "symbol_search", "module_report")}}, lens
    open_tui = json.loads((home / ".pi/agent/open-tui.json").read_text())
    assert open_tui == {"footerSegments": {"runtime": False, "cost": False, "extensionStatuses": False}}, open_tui
    config = json.loads((home / ".pi/agent/herdr-agents/config.json").read_text())
    repo_models = json.loads((Path(install).resolve().parents[1] / "pi/herdr-agents-models.json").read_text())
    assert config == {"panes": {"mode": "split", "direction": "right"}, "models": repo_models}, config
    assert not (home / ".pi/agent/herdr-agents/roles").exists()
    assert "claude-bridge/" not in (home / ".pi/agent/AGENTS.md").read_text()
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
  local backup_base="$fake_home/.local/state/weihung-agent-root/backups"
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
  [[ -n "$(find "$fake_home/.local/state/weihung-agent-root/backups" -path '*/providing-knowledge/SKILL.md')" ]] \
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
    (agent / "settings.json").write_text(json.dumps({"packages": ["git:github.com/wayne930242/pi-claude-bridge@old-commit", "npm:user-package", "npm:pi-lens"], "theme": "light", "enabledModels": ["user/model"], "terminal": {"showImages": False}, "powerline": {"welcome": False}, "compaction": {"keepRecentTokens": 30000, "modelOverrides": {"user/big": {"reserveTokens": 1}}}}))
    original_mcp = {"settings": {"namespaceProxyTools": True}, "mcpServers": {"codebase-memory-mcp": {"command": "cbm"}, "user": {"url": "https://example.test/mcp"}}}
    (agent / "mcp-adapter.json").write_text(json.dumps(original_mcp))
    pi_mcp = {"mcpServers": {"docs": {"url": "https://example.test/docs"}}}
    (agent / "mcp.json").write_text(json.dumps(pi_mcp))  # pi's own file, which the adapter also reads
    lens_path = home / ".pi-lens/config.json"
    lens_path.parent.mkdir()
    original_lens = {"lsp": {"enabled": False}, "tools": {"symbol_search": {"enabled": True}}}
    lens_path.write_text(json.dumps(original_lens))
    open_tui_path = agent / "open-tui.json"
    original_open_tui = {"cursorStyle": "bar", "footerSegments": {"cwd": True, "cost": True}}
    open_tui_path.write_text(json.dumps(original_open_tui))
    config = agent / "herdr-agents/config.json"
    config.parent.mkdir(parents=True, exist_ok=True)
    original_models = {"default": "user/model", "agents": {"scout": "user/scout"}}
    config.write_text(json.dumps({"models": original_models, "panes": {"mode": "tab"}, "other": True}))
    run(install, home, "--force")
    installed_packages = json.loads((agent / "settings.json").read_text())["packages"]
    assert "git:github.com/wayne930242/pi-claude-bridge@old-commit" not in installed_packages, "an earlier revision of a git pin is retired"
    assert any(isinstance(package, str) and package.startswith("git:github.com/wayne930242/pi-claude-bridge@b273512") for package in installed_packages), installed_packages
    assert [package for package in installed_packages if "pi-lens" in str(package)] == ["npm:pi-lens@4.3.0"], installed_packages
    assert json.loads((agent / "mcp.json").read_text()) == pi_mcp, "pi's mcp.json stays untouched"
    installed_mcp = json.loads((agent / "mcp-adapter.json").read_text())
    assert installed_mcp["mcpServers"]["codebase-memory-mcp"] == {"command": "cbm", "disabled": True}, installed_mcp
    assert installed_mcp["settings"]["namespaceProxyTools"] is False, installed_mcp
    assert json.loads(lens_path.read_text())["tools"]["symbol_search"] == {"enabled": False}
    installed_open_tui = json.loads(open_tui_path.read_text())
    assert installed_open_tui == {"cursorStyle": "bar", "footerSegments": {"cwd": True, "cost": False, "runtime": False, "extensionStatuses": False}}, installed_open_tui
    repo_models = json.loads((Path(install).resolve().parents[1] / "pi/herdr-agents-models.json").read_text())
    assert json.loads(config.read_text())["models"] == repo_models, "--force replaces the user's herdr-agents models"
    assert json.loads((agent / "settings.json").read_text())["enabledModels"] == ["user/model"], "pi's model settings are the user's"
    installed_compaction = json.loads((agent / "settings.json").read_text())["compaction"]
    assert installed_compaction == {"keepRecentTokens": 30000, "modelOverrides": {"user/big": {"reserveTokens": 1}, "claude-bridge/claude-opus-5-5": {"reserveTokens": 500000}, "claude-bridge/claude-sonnet-5-5": {"reserveTokens": 500000}}}, installed_compaction
    run(uninstall, home)
    assert (agent / "AGENTS.md").read_text() == "user instructions\n"
    settings = json.loads((agent / "settings.json").read_text())
    assert settings["packages"] == ["git:github.com/wayne930242/pi-claude-bridge@old-commit", "npm:user-package", "npm:pi-lens"], settings
    assert settings["theme"] == "light", settings
    assert settings["enabledModels"] == ["user/model"], settings
    assert "enableInstallTelemetry" not in settings, settings
    assert json.loads((agent / "mcp-adapter.json").read_text()) == original_mcp
    assert json.loads((agent / "mcp.json").read_text()) == pi_mcp
    assert json.loads(lens_path.read_text()) == original_lens
    assert json.loads(open_tui_path.read_text()) == original_open_tui
    assert settings["terminal"] == {"showImages": False}, settings
    assert settings["powerline"] == {"welcome": False}, settings
    assert settings["compaction"] == {"keepRecentTokens": 30000, "modelOverrides": {"user/big": {"reserveTokens": 1}}}, settings
    assert json.loads(config.read_text()) == {"models": original_models, "panes": {"mode": "tab"}, "other": True}
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
}

if [[ "${1:-}" == "" ]]; then
  run_all_tests
  printf 'install: pass\n'
else
  "$1"
fi
