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

    def test_handoff_commits_after_receiver_starts(self):
        spec = importlib.util.spec_from_file_location("pi_dispatch", ROOT / "scripts/pi-dispatch.py")
        dispatch = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dispatch)
        with tempfile.TemporaryDirectory() as directory:
            agent = Path(directory) / ".pi/agent"
            dispatch.LEDGER_DIR = agent / "dispatch-ledger"
            dispatch.HANDOFF_DIR = agent / "handoffs"
            dispatch.write_json(dispatch.ledger_path("owner"), [{
                "id": "child-1", "name": "worker", "task": "Task", "cwd": directory,
                "sessionFile": str(Path(directory) / "child.jsonl"), "status": "running",
            }])
            dispatch.new_pane = lambda *_args: "w1:p3"
            calls = []
            starts = 0

            def herdr(*args):
                nonlocal starts
                calls.append(args)
                if args[:2] == ("agent", "start"):
                    self.assertEqual(dispatch.read_ledger("owner")[0]["status"], "running")
                    starts += 1
                    if starts == 1:
                        raise RuntimeError('agent_pane_busy: shell is not ready')
                    transfer = next(dispatch.HANDOFF_DIR.glob("*.json"))
                    transfer.with_suffix(".ready").write_text("receiver")
                return {}

            dispatch.herdr = herdr
            dispatch.handoff("owner", directory, "Continue")
            self.assertEqual(starts, 2)
            self.assertEqual(dispatch.read_ledger("owner")[0]["status"], "transferred")

    def test_uncertain_receiver_start_keeps_original_owner(self):
        spec = importlib.util.spec_from_file_location("pi_dispatch_uncertain", ROOT / "scripts/pi-dispatch.py")
        dispatch = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dispatch)
        with tempfile.TemporaryDirectory() as directory:
            agent = Path(directory) / ".pi/agent"
            dispatch.LEDGER_DIR = agent / "dispatch-ledger"
            dispatch.HANDOFF_DIR = agent / "handoffs"
            dispatch.write_json(dispatch.ledger_path("owner"), [{
                "id": "child-uncertain", "name": "worker", "task": "Task", "cwd": directory,
                "sessionFile": str(Path(directory) / "child.jsonl"), "status": "running",
            }])
            dispatch.new_pane = lambda *_args: "w1:p3"
            dispatch.herdr = lambda *_args: (_ for _ in ()).throw(RuntimeError("timeout: startup may continue"))
            with self.assertRaisesRegex(RuntimeError, "timeout: startup may continue"):
                dispatch.handoff("owner", directory, "Continue")
            self.assertEqual(dispatch.read_ledger("owner")[0]["status"], "running")
            self.assertEqual(len(list(dispatch.HANDOFF_DIR.glob("*.json"))), 0)

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
            env = {"PATH": str(bin_dir) + os.pathsep + os.environ["PATH"]}
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
