"""Regression checks for the Pi migration review findings."""

import hashlib
import importlib.util
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
PI_TARGET = ROOT / "scripts/pi-target.py"
def fake_npm_install(args):
    """Produce what a successful `npm install --prefix` of team-toon-tack leaves behind."""
    if "--prefix" not in args:
        return
    prefix = Path(args[args.index("--prefix") + 1])
    skill = prefix / "node_modules/team-toon-tack/skills/managing-linear-tasks"
    skill.mkdir(parents=True, exist_ok=True)
    (skill / "SKILL.md").write_text("---\nname: managing-linear-tasks\n---\n")
    cli = prefix / "node_modules/.bin/ttt"
    cli.parent.mkdir(parents=True, exist_ok=True)
    cli.write_text("#!/bin/sh\n")
    cli.chmod(0o755)


def load_target() -> Any:
    spec = importlib.util.spec_from_file_location("pi_target_under_test", PI_TARGET)
    assert spec and spec.loader
    target = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(target)
    return target


def run_script(script, home, *args, env=None, check=True):
    return subprocess.run(
        ["bash", str(ROOT / "scripts" / script), "--home", str(home), *args],
        env={**os.environ, "HOME": str(home), **(env or {})},
        text=True, capture_output=True, check=check,
    )


class PiReviewFixes(unittest.TestCase):
    def test_uninstall_restores_present_null_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            settings_path = agent / "settings.json"
            settings_path.write_text(json.dumps({"defaultProvider": None, "theme": None}))
            run_script("install.sh", home, "--skip-external")
            run_script("install.sh", home, "--skip-external")
            run_script("uninstall.sh", home, "--skip-external")
            restored = json.loads(settings_path.read_text())
            self.assertIn("defaultProvider", restored)
            self.assertIsNone(restored["defaultProvider"])
            self.assertIn("theme", restored)
            self.assertIsNone(restored["theme"])
            self.assertNotIn("defaultModel", restored)

    def test_strategy_tables_mirror_pi_profiles(self):
        preferences = ROOT / "skills/managing-model-preferences"
        profiles = json.loads((ROOT / "pi/model-profiles.json").read_text())
        catalog = (preferences / "model-preference-profile.md").read_text()
        self.assertEqual(sorted(path.stem for path in (preferences / "strategies").glob("*.md")), sorted(profiles))
        for name, tiers in profiles.items():
            with self.subTest(strategy=name):
                content = (preferences / f"strategies/{name}.md").read_text()
                rows = [line for line in content.splitlines() if line.startswith("| ") and "`" in line]
                expected = [f"| {tier} | `{model}` | {thinking} |" for tier, (model, thinking) in tiers.items()]
                self.assertEqual(rows, expected)
                self.assertIn(f"[{name}](strategies/{name}.md)", catalog)
                self.assertNotIn("agent-kind", content)

    def test_install_links_skills_and_rules_then_uninstall_removes_them(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            run_script("install.sh", home, "--skip-external")
            self.assertEqual((home / ".pi/agent/rules").readlink(), ROOT / "rules")
            self.assertEqual((home / ".agents/skills/managing-model-preferences").readlink(), ROOT / "skills/managing-model-preferences")
            instructions = (home / ".pi/agent/AGENTS.md").read_text()
            for rule in (ROOT / "rules").glob("*.md"):
                self.assertIn(f"`{rule.name}`", instructions)
                self.assertFalse(rule.read_text().startswith("---"), rule.name)
            run_script("uninstall.sh", home, "--skip-external")
            self.assertFalse((home / ".pi/agent/rules").exists())
            self.assertFalse((home / ".agents").exists())
            self.assertFalse((home / ".pi/agent/.weihung-agent-root.json").exists())

    def test_all_tiers_have_distinct_task_fallbacks(self):
        target = load_target()
        profiles = json.loads((ROOT / "pi/model-profiles.json").read_text())
        for strategy, tiers in profiles.items():
            with self.subTest(strategy=strategy):
                target.active_strategy = lambda strategy=strategy: strategy
                _, default, _, tasks = target.routing()
                self.assertEqual(set(tasks), {"coding", "review", "recon", "qa", "architecture", "docs"})
                for tier, candidates in tasks.items():
                    self.assertEqual(candidates[0], tiers.get(tier, tiers["review"] if tier == "qa" else tiers["complex_unclear"])[0])
                    self.assertEqual(len(candidates), len(set(candidates)))
                self.assertEqual(len(target.default_candidates(default)), len(set(target.default_candidates(default))))
                instructions = target.instructions()
                for tier, (model, thinking) in tiers.items():
                    expected = ", ".join(target.candidates(model, tier))
                    self.assertIn(f"model `{expected}`; thinking `{thinking}`", instructions)

    def test_only_main_falls_back_to_opus_1m(self):
        target = load_target()
        profiles = json.loads((ROOT / "pi/model-profiles.json").read_text())
        one_m = {"main", "complex_clear", "complex_unclear", "academic"}
        for strategy, tiers in profiles.items():
            for tier, (model, _) in tiers.items():
                with self.subTest(strategy=strategy, tier=tier):
                    self.assertNotEqual(model == target.OPUS_1M and tier not in one_m, True)
                    if model == target.LUNA:
                        self.assertEqual(target.candidates(model, tier)[1], target.HAIKU)
        self.assertEqual(target.candidates("openai-codex/gpt-6.1-sol", "main")[1], target.OPUS_1M)
        self.assertEqual(target.candidates("openai-codex/gpt-6.1-sol", "complex_clear")[1], target.OPUS_200K)
        self.assertEqual(target.candidates("openai-codex/gpt-6-astra", "architecture")[1], target.OPUS_200K)
        self.assertEqual(target.candidates("openai-codex/gpt-6.1-sol", "review")[1], target.OPUS_200K)
        self.assertEqual(target.candidates("openai-codex/gpt-6.1-sol", "ui")[1], target.OPUS_200K)

    def test_upstream_bridge_pin_is_retired_for_the_fork(self):
        upstream = "git:github.com/elidickinson/pi-claude-bridge@227f5eb4450a070dfbc083a7fe75b8b35366b941"
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            (agent / "settings.json").write_text(json.dumps({"packages": [upstream]}))
            run_script("install.sh", home, "--skip-external")
            installed = json.loads((agent / "settings.json").read_text())["packages"]
            self.assertEqual([item for item in installed if "pi-claude-bridge" in item],
                             ["git:github.com/wayne930242/pi-claude-bridge@08f0e83bd0032cf9dd4acb5664591d589327ea45"])

    def test_install_under_the_former_name_moves_to_the_new_one(self):
        import shutil
        with tempfile.TemporaryDirectory() as directory:
            # The installer resolves its home, and macOS temporary directories sit behind /var -> /private/var.
            base = Path(directory).resolve()
            home = base / "home"
            legacy_root = base / "weihung-user-claude"
            root = base / "weihung-agent-root"
            shutil.copytree(ROOT, root, ignore=shutil.ignore_patterns(".git", "node_modules", "__pycache__"))
            agent = home / ".pi/agent"
            share = home / ".local/share/weihung-user-claude"
            backup = home / ".local/state/weihung-user-claude/backups/1/.pi/agent/AGENTS.md"
            (share / "pi-skills").mkdir(parents=True)
            backup.parent.mkdir(parents=True)
            backup.write_text("user instructions")
            (agent / "skills").mkdir(parents=True)
            (agent / "skills/pi-skills").symlink_to(share / "pi-skills")
            (agent / "rules").symlink_to(legacy_root / "rules")
            (home / ".agents/skills").mkdir(parents=True)
            (home / ".agents/skills/reflecting-to-root").symlink_to(legacy_root / "skills/reflecting-to-root")
            (agent / "settings.json").write_text(json.dumps({"packages": ["npm:user-package", "../../../weihung-user-claude"]}))
            (agent / ".weihung-user-claude.json").write_text(json.dumps({
                "instructions_backup": str(backup),
                "pi_skills_clone": str(share / "pi-skills"),
                "ported_resources": {".pi/agent/skills/pi-skills": {"installed": str(share / "pi-skills"), "link": True}},
            }))
            subprocess.run([sys.executable, str(root / "scripts/pi-target.py"), "migrate", "--home", str(home)], check=True)
            new_share = home / ".local/share/weihung-agent-root"
            state = json.loads((agent / ".weihung-agent-root.json").read_text())
            self.assertFalse((agent / ".weihung-user-claude.json").exists())
            self.assertFalse(share.exists())
            self.assertEqual(Path(state["instructions_backup"]).read_text(), "user instructions")
            self.assertEqual(state["pi_skills_clone"], str(new_share / "pi-skills"))
            self.assertEqual(state["ported_resources"][".pi/agent/skills/pi-skills"]["installed"], str(new_share / "pi-skills"))
            self.assertEqual(os.readlink(agent / "skills/pi-skills"), str(new_share / "pi-skills"))
            self.assertEqual(os.readlink(agent / "rules"), str(root / "rules"))
            self.assertEqual(os.readlink(home / ".agents/skills/reflecting-to-root"), str(root / "skills/reflecting-to-root"))
            self.assertEqual(json.loads((agent / "settings.json").read_text())["packages"], ["npm:user-package", str(root)])

            (agent / ".weihung-user-claude.json").write_text("{}")
            conflict = subprocess.run([sys.executable, str(root / "scripts/pi-target.py"), "migrate", "--home", str(home)],
                                      capture_output=True, text=True, check=False)
            self.assertNotEqual(conflict.returncode, 0)
            self.assertIn("merge them by hand", conflict.stderr)

    def test_earlier_straw_boss_revisions_are_retired_for_the_pin(self):
        for earlier in ("git:github.com/wayne930242/straw-boss", "git:github.com/wayne930242/straw-boss@old-commit"):
            with self.subTest(earlier=earlier), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                agent = home / ".pi/agent"
                agent.mkdir(parents=True)
                (agent / "settings.json").write_text(json.dumps({"packages": [earlier]}))
                run_script("install.sh", home, "--skip-external")
                installed = json.loads((agent / "settings.json").read_text())["packages"]
                pin = re.search(r'STRAW_BOSS_SOURCE = "([^"]+)"', PI_TARGET.read_text()).group(1)
                self.assertEqual([item for item in installed if "straw-boss" in item], [pin])

    def test_company_plugins_are_managed_when_present_and_skipped_when_absent(self):
        variables = {"mp-infra": "PI_MP_INFRA_ROOT", "sdlc": "PI_SDLC_ROOT"}
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            roots = {name: home / "marketplace/plugins" / name for name in variables}
            for root in roots.values():
                root.mkdir(parents=True)
                (root / "package.json").write_text("{}")
            env = {variable: str(roots[name]) for name, variable in variables.items()}
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            for _ in range(2):
                run_script("install.sh", home, "--skip-external", env=env)
            installed = json.loads((agent / "settings.json").read_text())["packages"]
            for root in roots.values():
                self.assertEqual(installed.count(str(root.resolve())), 1)
            # The checkout goes away: the next install drops the entry instead of leaving Pi a missing package.
            (roots["sdlc"] / "package.json").unlink()
            result = run_script("install.sh", home, "--skip-external", env=env)
            self.assertIn("sdlc not found", result.stderr)
            installed = json.loads((agent / "settings.json").read_text())["packages"]
            self.assertNotIn(str(roots["sdlc"].resolve()), installed)
            self.assertIn(str(roots["mp-infra"].resolve()), installed)
            run_script("uninstall.sh", home, "--skip-external", env=env)
            settings = agent / "settings.json"
            remaining = json.loads(settings.read_text()).get("packages", []) if settings.exists() else []
            self.assertFalse([item for item in remaining if "marketplace" in str(item)])
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            env = {variable: str(home / "missing" / name) for name, variable in variables.items()}
            result = run_script("install.sh", home, "--skip-external", env=env)
            self.assertIn("mp-infra not found", result.stderr)
            self.assertIn("sdlc not found", result.stderr)
            installed = json.loads((home / ".pi/agent/settings.json").read_text())["packages"]
            self.assertFalse([item for item in installed if "marketplace" in str(item) or "/missing/" in str(item)])

    def test_mp_infra_port_from_earlier_installs_is_retired_for_the_package(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            plugin = home / "marketplace/plugins/mp-infra"
            (plugin / "skills/nomad").mkdir(parents=True)
            (plugin / "package.json").write_text("{}")
            env = {"PI_MP_INFRA_ROOT": str(plugin), "PI_SDLC_ROOT": str(home / "no-sdlc")}
            run_script("install.sh", home, "--skip-external", env=env)
            # Reproduce what an install from before mp-infra became a package left behind.
            marker = agent / ".weihung-agent-root.json"
            state = json.loads(marker.read_text())
            (agent / "skills").mkdir(parents=True, exist_ok=True)
            (agent / "skills/nomad").symlink_to(plugin / "skills/nomad")
            (agent / "mp-infra.json").write_text(json.dumps({"root": str(plugin)}))
            ported = state.setdefault("ported_resources", {})
            ported[".pi/agent/skills/nomad"] = {"installed": str(plugin / "skills/nomad"), "link": True}
            ported[".pi/agent/mp-infra.json"] = {"installed": hashlib.sha256((agent / "mp-infra.json").read_bytes()).hexdigest(), "link": False}
            marker.write_text(json.dumps(state))
            run_script("install.sh", home, "--skip-external", env=env)
            self.assertFalse((agent / "skills/nomad").is_symlink())
            self.assertFalse((agent / "mp-infra.json").exists())
            resources = json.loads(marker.read_text())["ported_resources"]
            self.assertNotIn(".pi/agent/skills/nomad", resources)
            self.assertNotIn(".pi/agent/mp-infra.json", resources)

    def test_codebase_memory_port_from_earlier_installs_is_retired(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            run_script("install.sh", home, "--skip-external")
            marker = agent / ".weihung-agent-root.json"
            # Reproduce what an install from before codebase-memory was dropped left behind.
            (agent / "extensions").mkdir(parents=True, exist_ok=True)
            (agent / "skills/codebase-memory").mkdir(parents=True, exist_ok=True)
            (agent / "extensions/cbmem.ts").write_text("const BIN = 'x';\n")
            (agent / "skills/codebase-memory/SKILL.md").write_text("---\nname: codebase-memory\n---\n")
            state = json.loads(marker.read_text())
            ported = state.setdefault("ported_resources", {})
            for key in (".pi/agent/extensions/cbmem.ts", ".pi/agent/skills/codebase-memory/SKILL.md"):
                ported[key] = {"installed": hashlib.sha256((home / key).read_bytes()).hexdigest(), "link": False}
            marker.write_text(json.dumps(state))
            run_script("install.sh", home, "--skip-external")
            self.assertFalse((agent / "extensions/cbmem.ts").exists())
            self.assertFalse((agent / "skills/codebase-memory").exists())
            resources = json.loads(marker.read_text())["ported_resources"]
            self.assertNotIn(".pi/agent/extensions/cbmem.ts", resources)
            self.assertNotIn(".pi/agent/skills/codebase-memory/SKILL.md", resources)

    def test_upgrade_retires_the_powerline_footer_and_notify(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            settings = agent / "settings.json"
            settings.write_text(json.dumps({"packages": ["npm:user-package"], "powerline": {"welcome": False}}))
            run_script("install.sh", home, "--skip-external")
            marker = agent / ".weihung-agent-root.json"
            # Reproduce what an install from before pi-open-tui left behind.
            state = json.loads(marker.read_text())
            state.update(previous_powerline={"welcome": False},
                         installed_powerline={"welcome": False, "queue": {"compactPromptMode": "native"}})
            marker.write_text(json.dumps(state))
            current = json.loads(settings.read_text())
            current["packages"] += ["npm:pi-powerline-footer", "npm:pi-notify"]
            current["powerline"] = {"welcome": False, "queue": {"compactPromptMode": "native"}}
            settings.write_text(json.dumps(current))
            run_script("install.sh", home, "--skip-external")
            upgraded = json.loads(settings.read_text())
            self.assertNotIn("npm:pi-powerline-footer", upgraded["packages"])
            self.assertNotIn("npm:pi-notify", upgraded["packages"])
            self.assertIn("npm:pi-open-tui@0.3.9", upgraded["packages"])
            self.assertIn("npm:user-package", upgraded["packages"])
            self.assertEqual(upgraded["powerline"], {"welcome": False})
            run_script("uninstall.sh", home, "--skip-external")
            restored = json.loads(settings.read_text())
            self.assertEqual(restored["packages"], ["npm:user-package"])
            self.assertEqual(restored["powerline"], {"welcome": False})

    def test_upgrade_replaces_the_pi_code_fork_with_its_npm_release(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            settings = agent / "settings.json"
            settings.write_text(json.dumps({"packages": ["npm:user-package"]}))
            run_script("install.sh", home, "--skip-external")
            # Reproduce the fork an earlier install registered.
            current = json.loads(settings.read_text())
            current["packages"] = [package for package in current["packages"] if "pi-code@" not in json.dumps(package)]
            current["packages"].append({"source": "git:github.com/wayne930242/pi-code@b88ba30aa987d5e34ddffd4c6c469f78711ac711",
                                        "extensions": ["extensions/claude-rules.ts"]})
            settings.write_text(json.dumps(current))
            run_script("install.sh", home, "--skip-external")
            upgraded = json.loads(settings.read_text())["packages"]
            self.assertEqual([package for package in upgraded if "pi-code@" in json.dumps(package)],
                             [{"source": "npm:pi-code@1.2.1",
                               "extensions": ["extensions/claude-rules.ts"]}])
            self.assertIn("npm:user-package", upgraded)

    def test_upgrade_replaces_pi_usage_with_pi_quotas(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            settings = agent / "settings.json"
            settings.write_text(json.dumps({"packages": ["npm:user-package"]}))
            run_script("install.sh", home, "--skip-external")
            # Earlier installs registered the npm release, then the pi-usage fork.
            current = json.loads(settings.read_text())
            current["packages"] += ["npm:pi-usage", "git:github.com/wayne930242/pi-usage@a683c242cf42801c484c9ae6eeb3accdf4b7c696"]
            settings.write_text(json.dumps(current))
            run_script("install.sh", home, "--skip-external")
            packages = json.loads(settings.read_text())["packages"]
            self.assertEqual([item for item in packages if "pi-usage" in item or "pi-quotas" in item],
                             ["git:github.com/wayne930242/pi-quotas@caa30da4f6d3d3e2a57edbb85e8de1f856f7ee6b"])
            self.assertIn("npm:user-package", packages)

    def test_upgrade_pins_packages_and_retires_replaced_ones(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            settings = agent / "settings.json"
            settings.write_text(json.dumps({"packages": ["npm:user-package"]}))
            run_script("install.sh", home, "--skip-external")
            # Reproduce the unpinned packages and marker an install before pinning left behind.
            marker = agent / ".weihung-agent-root.json"
            state = json.loads(marker.read_text())
            for key in ("previous_settings", "previous_ui_settings"):
                state[key] = {name: value for name, value in state[key].items() if name not in ("enabledModels", "enableInstallTelemetry")}
                state.pop(f"{key}_present")
            marker.write_text(json.dumps(state))
            current = json.loads(settings.read_text())
            current["packages"] = ["npm:user-package", "npm:pi-lens", "npm:pi-web-access@0.31.0",
                                   "git:github.com/wayne930242/pi-web-access@3b13c02cb2ece014b432bece21b9a380ed4c240c", "npm:@capdiem/pi-todo", "npm:catppuccin-pi-theme"]
            current.pop("enabledModels")
            current.pop("enableInstallTelemetry")
            settings.write_text(json.dumps(current))
            run_script("install.sh", home, "--skip-external")
            upgraded = json.loads(settings.read_text())
            sources = [item["source"] if isinstance(item, dict) else item for item in upgraded["packages"]]
            self.assertEqual([item for item in sources if "pi-lens" in item], ["npm:pi-lens@4.3.0"])
            self.assertFalse(any("pi-todo" in item or "catppuccin" in item for item in sources), sources)
            self.assertIn("npm:@juicesharp/rpiv-todo@2.12.0", sources)
            self.assertEqual([item for item in sources if "pi-web-access" in item],
                             ["npm:pi-web-access@0.33.0"])
            self.assertIs(upgraded["enableInstallTelemetry"], False)
            run_script("uninstall.sh", home, "--skip-external")
            restored = json.loads(settings.read_text())
            self.assertEqual(restored["packages"], ["npm:user-package"])
            self.assertNotIn("enabledModels", restored)
            self.assertNotIn("enableInstallTelemetry", restored)

    def test_builtin_mcp_is_disabled_for_the_adapter_and_restored(self):
        for before in (None, ["extra.ts"], ["-builtin:mcp"]):
            with self.subTest(before=before), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                agent = home / ".pi/agent"
                agent.mkdir(parents=True)
                settings = agent / "settings.json"
                settings.write_text(json.dumps({} if before is None else {"extensions": before}))
                run_script("install.sh", home, "--skip-external")
                installed = json.loads(settings.read_text())["extensions"]
                self.assertEqual(installed.count("-builtin:mcp"), 1, installed)
                self.assertEqual([item for item in installed if item != "-builtin:mcp"], [item for item in before or [] if item != "-builtin:mcp"])
                run_script("install.sh", home, "--skip-external")
                self.assertEqual(json.loads(settings.read_text())["extensions"], installed)
                run_script("uninstall.sh", home, "--skip-external")
                self.assertEqual(json.loads(settings.read_text()).get("extensions"), before)

    def test_package_identity_ignores_the_npm_version(self):
        target = load_target()
        agent = Path("/unused")
        self.assertEqual(target.package_id("npm:pi-lens@4.3.0", agent), "npm:pi-lens")
        self.assertEqual(target.package_id("npm:@scope/name@1.0.0", agent), "npm:@scope/name")
        self.assertEqual(target.package_id("npm:@scope/name", agent), "npm:@scope/name")
        self.assertEqual(target.package_id({"source": "npm:pi-lens", "skills": []}, agent), "npm:pi-lens")

    def test_user_owned_powerline_survives_install(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            settings = agent / "settings.json"
            settings.write_text(json.dumps({"packages": ["npm:pi-powerline-footer"]}))
            run_script("install.sh", home, "--skip-external")
            self.assertIn("npm:pi-powerline-footer", json.loads(settings.read_text())["packages"])

    def test_previous_git_bridge_revision_is_restored(self):
        old = "git:github.com/elidickinson/pi-claude-bridge@old-commit"
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            (agent / "settings.json").write_text(json.dumps({"packages": [old, "npm:user-package"]}))
            run_script("install.sh", home, "--skip-external")
            installed = json.loads((agent / "settings.json").read_text())["packages"]
            self.assertNotIn(old, installed)
            self.assertEqual(sum("pi-claude-bridge" in item for item in installed), 1)
            run_script("uninstall.sh", home, "--skip-external")
            self.assertEqual(json.loads((agent / "settings.json").read_text())["packages"], [old, "npm:user-package"])

    def test_external_git_switch_keeps_the_new_checkout(self):
        target = load_target()
        old = "git:github.com/elidickinson/pi-claude-bridge@old-commit"
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            settings = agent / "settings.json"
            settings.write_text(json.dumps({"packages": [old]}))
            removals = []

            def fake_run(args, _home):
                if args[0] == "npm":
                    fake_npm_install(args)
                if args[:2] == ["pi", "install"]:
                    current = json.loads(settings.read_text())
                    current.setdefault("packages", []).append(args[2])
                    settings.write_text(json.dumps(current))
                if args[:2] == ["pi", "remove"]:
                    removals.append(args[2])

            target.run = fake_run
            target.install(home, skip_external=False, force=False)
            self.assertNotIn(old, json.loads(settings.read_text())["packages"])
            self.assertNotIn(old, removals)

    def test_failed_external_install_can_retry_and_uninstall(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            bin_dir = home / "bin"
            bin_dir.mkdir()
            for name in ("npm", "herdr", "pi"):
                script = bin_dir / name
                script.write_text("#!/bin/sh\n[ -e \"$HOME/fail-once\" ] && { rm \"$HOME/fail-once\"; exit 4; }\n"
                                  + (f"exec python3 {Path(__file__).resolve()} fake-npm \"$@\"\n" if name == "npm" else "exit 0\n"))
                script.chmod(0o755)
            (home / "fail-once").write_text("")
            pi_skills = home / "pi-skills-fixture"
            (pi_skills / "brave-search").mkdir(parents=True)
            (pi_skills / "brave-search/SKILL.md").write_text("---\nname: brave-search\ndescription: Test skill\n---\n")
            subprocess.run(["git", "init", "-q", str(pi_skills)], check=True)
            subprocess.run(["git", "-C", str(pi_skills), "add", "."], check=True)
            subprocess.run(["git", "-C", str(pi_skills), "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"], check=True)
            env = {"PATH": str(bin_dir) + os.pathsep + os.environ["PATH"], "PI_SKILLS_GIT": str(pi_skills)}
            command = ["python3", str(PI_TARGET), "install", "--home", str(home)]
            failed = subprocess.run(command, env={**os.environ, "HOME": str(home), **env},
                                    text=True, capture_output=True, check=False)
            self.assertNotEqual(failed.returncode, 0)
            marker = home / ".pi/agent/.weihung-agent-root.json"
            self.assertTrue(marker.exists())
            self.assertFalse(json.loads(marker.read_text())["integration_installed"])
            run_script("uninstall.sh", home, "--skip-external")
            self.assertFalse(marker.exists())
            (home / "fail-once").write_text("")
            failed = subprocess.run(command, env={**os.environ, "HOME": str(home), **env},
                                    text=True, capture_output=True, check=False)
            self.assertNotEqual(failed.returncode, 0)
            subprocess.run(command, env={**os.environ, "HOME": str(home), **env}, check=True)
            run_script("uninstall.sh", home, "--skip-external")
            self.assertFalse(marker.exists())

    def test_malformed_json_names_the_file(self):
        target = load_target()
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text("{broken")
            with self.assertRaisesRegex(ValueError, f"{path} is not valid JSON"):
                target.read_json(path)

    def test_backup_survives_a_failed_link_and_is_restored(self):
        target = load_target()
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            destination = home / ".pi/agent/skills/pi-skills"
            destination.parent.mkdir(parents=True)
            destination.write_text("user copy\n")
            source = home / "clone"
            source.mkdir()
            with mock.patch.object(Path, "symlink_to", side_effect=OSError("link failed")), self.assertRaises(OSError):
                    target.managed_resource(home, {}, destination, source, force=True, link=True)
            state = target.read_json(home / target.MARKER)
            target.managed_resource(home, state, destination, source, force=True, link=True)
            target.uninstall_ported_resources(home, target.read_json(home / target.MARKER))
            self.assertEqual(destination.read_text(), "user copy\n")

    def test_failed_restore_is_retried_by_the_next_uninstall(self):
        target = load_target()
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            destination = home / ".pi/agent/skills/pi-skills"
            destination.parent.mkdir(parents=True)
            destination.write_text("user copy\n")
            source = home / "clone"
            source.mkdir()
            target.managed_resource(home, {}, destination, source, force=True, link=True)
            state = target.read_json(home / target.MARKER)
            with mock.patch.object(target.shutil, "move", side_effect=OSError("move failed")), self.assertRaises(OSError):
                    target.uninstall_ported_resources(home, state)
            target.uninstall_ported_resources(home, state)
            self.assertEqual(destination.read_text(), "user copy\n")

    def test_instructions_backup_survives_a_failed_install_and_uninstall(self):
        target = load_target()
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            instructions = home / ".pi/agent/AGENTS.md"
            instructions.parent.mkdir(parents=True)
            instructions.write_text("user instructions\n")
            with mock.patch.object(target, "update_mcp", side_effect=ValueError("broken mcp.json")), self.assertRaises(ValueError):
                    target.install(home, skip_external=True, force=True)
            target.install(home, skip_external=True, force=True)
            real_move = target.shutil.move

            def fail_on_instructions(source, destination):
                if Path(destination) == instructions:
                    raise OSError("move failed")
                return real_move(source, destination)

            with mock.patch.object(target.shutil, "move", side_effect=fail_on_instructions), self.assertRaises(OSError):
                    target.uninstall(home, skip_external=True)
            target.uninstall(home, skip_external=True)
            self.assertEqual(instructions.read_text(), "user instructions\n")


if __name__ == "__main__":
    if sys.argv[1:2] == ["fake-npm"]:
        fake_npm_install(sys.argv[2:])
    else:
        unittest.main()
