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
                roles = target.tier_roles(tiers)
                self.assertEqual(set(roles), {f"{tier}.md" for tier in tiers if tier != "main"})
                for tier, (model, thinking) in tiers.items():
                    self.assertNotIn(model, instructions)
                    if tier == "main":
                        continue
                    expected = ", ".join(target.candidates(model, tier))
                    self.assertIn(f"\nname: {tier}\n", roles[f"{tier}.md"])
                    self.assertIn(f"\nmodel: {expected}\nthinking: {thinking}\n", roles[f"{tier}.md"])
                for role, tier in target.ROLE_TIERS.items():
                    self.assertIn(tier, tiers, role)

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

    def test_earlier_straw_boss_revisions_are_retired_for_the_pin(self):
        for earlier in ("git:github.com/wayne930242/straw-boss", "git:github.com/wayne930242/straw-boss@old-commit"):
            with self.subTest(earlier=earlier), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                agent = home / ".pi/agent"
                agent.mkdir(parents=True)
                (agent / "settings.json").write_text(json.dumps({"packages": [earlier]}))
                run_script("install.sh", home, "--skip-external")
                installed = json.loads((agent / "settings.json").read_text())["packages"]
                declaration = re.search(r'STRAW_BOSS_SOURCE = "([^"]+)"', PI_TARGET.read_text())
                if declaration is None:
                    self.fail("STRAW_BOSS_SOURCE is not declared in pi-target.py")
                self.assertEqual([item for item in installed if "straw-boss" in item], [declaration.group(1)])

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

    def test_upgrade_pins_unpinned_packages_and_reads_an_old_marker(self):
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
            current["packages"] = ["npm:user-package", "npm:pi-lens", "npm:pi-web-access@0.31.0"]
            current.pop("enabledModels")
            current.pop("enableInstallTelemetry")
            settings.write_text(json.dumps(current))
            run_script("install.sh", home, "--skip-external")
            upgraded = json.loads(settings.read_text())
            sources = [item["source"] if isinstance(item, dict) else item for item in upgraded["packages"]]
            self.assertEqual([item for item in sources if "pi-lens" in item], ["npm:pi-lens@4.3.0"])
            self.assertEqual([item for item in sources if "pi-web-access" in item],
                             ["npm:pi-web-access@0.35.0"])
            self.assertIs(upgraded["enableInstallTelemetry"], False)
            run_script("uninstall.sh", home, "--skip-external")
            restored = json.loads(settings.read_text())
            self.assertEqual(restored["packages"], ["npm:user-package"])
            self.assertNotIn("enabledModels", restored)
            self.assertNotIn("enableInstallTelemetry", restored)

    def test_mcp_config_is_the_adapter_file_and_leaves_pi_mcp_json_alone(self):
        with tempfile.TemporaryDirectory() as directory:
            agent = Path(directory) / ".pi/agent"
            agent.mkdir(parents=True)
            target = load_target()
            self.assertEqual(target.mcp_config_path(agent), agent / "mcp-adapter.json")
            (agent / "mcp.json").write_text('{"mcpServers": {"user": {}}}')
            self.assertEqual(target.mcp_config_path(agent), agent / "mcp-adapter.json")
            self.assertEqual((agent / "mcp.json").read_text(), '{"mcpServers": {"user": {}}}')
            self.assertFalse((agent / "mcp-adapter.json").exists())

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

    def test_previous_git_bridge_revision_is_restored(self):
        old = "git:github.com/wayne930242/pi-claude-bridge@old-commit"
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
        old = "git:github.com/wayne930242/pi-claude-bridge@old-commit"
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
