"""Regression checks for the Pi migration review findings."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
PI_TARGET = ROOT / "scripts/pi-target.py"
FAKE_CBMEM = """#!/usr/bin/env python3
import os
from pathlib import Path
home = Path(os.environ['HOME'])
(home / '.pi/agent/extensions').mkdir(parents=True, exist_ok=True)
(home / '.pi/agent/skills/codebase-memory').mkdir(parents=True, exist_ok=True)
(home / '.pi/agent/extensions/cbmem.ts').write_text("const BIN = '" + str(home / '.local/bin/codebase-memory-mcp') + "';\\n")
(home / '.pi/agent/skills/codebase-memory/SKILL.md').write_text('---\\nname: codebase-memory\\n---\\n')
"""


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


def seed_codebase_memory(home):
    binary = home / ".local/bin/codebase-memory-mcp"
    binary.parent.mkdir(parents=True, exist_ok=True)
    binary.write_text(FAKE_CBMEM)
    binary.chmod(0o755)


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
            self.assertFalse((home / ".pi/agent/.weihung-user-claude.json").exists())

    def test_all_tiers_have_distinct_task_fallbacks(self):
        spec = importlib.util.spec_from_file_location("pi_target", PI_TARGET)
        target = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(target)
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

    def test_only_main_and_complex_tiers_fall_back_to_opus_1m(self):
        spec = importlib.util.spec_from_file_location("pi_target_tiers", PI_TARGET)
        target = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(target)
        profiles = json.loads((ROOT / "pi/model-profiles.json").read_text())
        one_m = {"main", "complex_clear", "complex_unclear", "academic"}
        for strategy, tiers in profiles.items():
            for tier, (model, _) in tiers.items():
                with self.subTest(strategy=strategy, tier=tier):
                    self.assertNotEqual(model == target.OPUS_1M and tier not in one_m, True)
                    if model == target.LUNA:
                        self.assertEqual(target.candidates(model, tier)[1], target.HAIKU)
        self.assertEqual(target.candidates("openai-codex/gpt-6-sol", "complex_clear")[1], target.OPUS_1M)
        self.assertEqual(target.candidates("openai-codex/gpt-6-astra", "architecture")[1], target.OPUS_1M)
        self.assertEqual(target.candidates("openai-codex/gpt-6-sol", "review")[1], target.OPUS_200K)
        self.assertEqual(target.candidates("openai-codex/gpt-6-sol", "ui")[1], target.OPUS_200K)

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
                             ["git:github.com/wayne930242/pi-claude-bridge@2f00cce984508e8bc1ea07ff98adc9c3873c709e"])

    def test_earlier_straw_boss_revisions_are_retired_for_the_pin(self):
        for earlier in ("git:github.com/wayne930242/straw-boss", "git:github.com/wayne930242/straw-boss@old-commit"):
            with self.subTest(earlier=earlier), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                agent = home / ".pi/agent"
                agent.mkdir(parents=True)
                (agent / "settings.json").write_text(json.dumps({"packages": [earlier]}))
                run_script("install.sh", home, "--skip-external")
                installed = json.loads((agent / "settings.json").read_text())["packages"]
                self.assertEqual([item for item in installed if "straw-boss" in item],
                                 ["git:github.com/wayne930242/straw-boss@3d0fceb216ecadc3ed6a22d3b2a82dbd3fb3cd3a"])

    def test_upgrade_retires_the_powerline_footer_and_notify(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            settings = agent / "settings.json"
            settings.write_text(json.dumps({"packages": ["npm:user-package"], "powerline": {"welcome": False}}))
            run_script("install.sh", home, "--skip-external")
            marker = agent / ".weihung-user-claude.json"
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

    def test_upgrade_replaces_npm_pi_usage_with_the_fork(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            settings = agent / "settings.json"
            settings.write_text(json.dumps({"packages": ["npm:user-package"]}))
            run_script("install.sh", home, "--skip-external")
            # An install from before the fork registered the npm release.
            current = json.loads(settings.read_text())
            current["packages"].append("npm:pi-usage")
            settings.write_text(json.dumps(current))
            run_script("install.sh", home, "--skip-external")
            usage = [item for item in json.loads(settings.read_text())["packages"] if "pi-usage" in item]
            self.assertEqual(usage, ["git:github.com/wayne930242/pi-usage@a683c242cf42801c484c9ae6eeb3accdf4b7c696"])

    def test_upgrade_pins_packages_and_retires_replaced_ones(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            settings = agent / "settings.json"
            settings.write_text(json.dumps({"packages": ["npm:user-package"]}))
            run_script("install.sh", home, "--skip-external")
            # Reproduce the unpinned packages and marker an install before pinning left behind.
            marker = agent / ".weihung-user-claude.json"
            state = json.loads(marker.read_text())
            for key in ("previous_settings", "previous_ui_settings"):
                state[key] = {name: value for name, value in state[key].items() if name not in ("enabledModels", "enableInstallTelemetry")}
                state.pop(f"{key}_present")
            marker.write_text(json.dumps(state))
            current = json.loads(settings.read_text())
            current["packages"] = ["npm:user-package", "npm:pi-lens", "npm:pi-web-access@0.31.0", "npm:@capdiem/pi-todo", "npm:catppuccin-pi-theme"]
            current.pop("enabledModels")
            current.pop("enableInstallTelemetry")
            settings.write_text(json.dumps(current))
            run_script("install.sh", home, "--skip-external")
            upgraded = json.loads(settings.read_text())
            sources = [item["source"] if isinstance(item, dict) else item for item in upgraded["packages"]]
            self.assertEqual([item for item in sources if "pi-lens" in item], ["npm:pi-lens@4.3.0"])
            self.assertFalse(any("pi-todo" in item or "catppuccin" in item for item in sources), sources)
            self.assertIn("npm:@juicesharp/rpiv-todo@2.11.0", sources)
            self.assertEqual([item for item in sources if "pi-web-access" in item],
                             ["git:github.com/wayne930242/pi-web-access@3b13c02cb2ece014b432bece21b9a380ed4c240c"])
            self.assertIs(upgraded["enableInstallTelemetry"], False)
            run_script("uninstall.sh", home, "--skip-external")
            restored = json.loads(settings.read_text())
            self.assertEqual(restored["packages"], ["npm:user-package"])
            self.assertNotIn("enabledModels", restored)
            self.assertNotIn("enableInstallTelemetry", restored)

    def test_package_identity_ignores_the_npm_version(self):
        spec = importlib.util.spec_from_file_location("pi_target_identity", PI_TARGET)
        target = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(target)
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
        spec = importlib.util.spec_from_file_location("pi_target_git", PI_TARGET)
        target = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(target)
        old = "git:github.com/elidickinson/pi-claude-bridge@old-commit"
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            settings = agent / "settings.json"
            settings.write_text(json.dumps({"packages": [old]}))
            removals = []

            seed_codebase_memory(home)

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
            seed_codebase_memory(home)
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
                                    text=True, capture_output=True)
            self.assertNotEqual(failed.returncode, 0)
            marker = home / ".pi/agent/.weihung-user-claude.json"
            self.assertTrue(marker.exists())
            self.assertFalse(json.loads(marker.read_text())["integration_installed"])
            run_script("uninstall.sh", home, "--skip-external")
            self.assertFalse(marker.exists())
            (home / "fail-once").write_text("")
            failed = subprocess.run(command, env={**os.environ, "HOME": str(home), **env},
                                    text=True, capture_output=True)
            self.assertNotEqual(failed.returncode, 0)
            subprocess.run(command, env={**os.environ, "HOME": str(home), **env}, check=True)
            run_script("uninstall.sh", home, "--skip-external")
            self.assertFalse(marker.exists())


if __name__ == "__main__":
    if sys.argv[1:2] == ["fake-npm"]:
        fake_npm_install(sys.argv[2:])
    else:
        unittest.main()
