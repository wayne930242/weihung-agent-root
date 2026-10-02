"""Install and uninstall end to end: settings round trips, retries, and the generated AGENTS.md."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pi_root import configs, jsonfile, steps
from support.pi import FAKE_NPM, PI_TARGET, ROOT, run_script


class StepTests(unittest.TestCase):
    def test_uninstall_restores_the_steps_in_reverse_install_order(self):
        calls = []
        recording = tuple(steps.Step(step.name, lambda ctx, name=step.name: calls.append(("apply", name)),
                                     lambda ctx, name=step.name: calls.append(("restore", name))) for step in steps.STEPS)
        with tempfile.TemporaryDirectory() as directory, mock.patch.object(steps, "STEPS", recording):
            home = Path(directory)
            steps.install(home, skip_external=True, force=False)
            self.assertTrue((home / ".pi/agent/.weihung-agent-root.json").exists(), "install saves the marker after each step")
            steps.uninstall(home, skip_external=True)
            self.assertFalse((home / ".pi/agent/.weihung-agent-root.json").exists())
        names = [step.name for step in steps.STEPS]
        self.assertEqual(calls, [("apply", name) for name in names] + [("restore", name) for name in reversed(names)])

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

    def test_malformed_json_names_the_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text("{broken")
            with self.assertRaisesRegex(ValueError, f"{path} is not valid JSON"):
                jsonfile.read_json(path)

    def test_failed_external_install_can_retry_and_uninstall(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            bin_dir = home / "bin"
            bin_dir.mkdir()
            for name in ("npm", "herdr", "pi"):
                script = bin_dir / name
                script.write_text("#!/bin/sh\n[ -e \"$HOME/fail-once\" ] && { rm \"$HOME/fail-once\"; exit 4; }\n"
                                  + (f"exec python3 {FAKE_NPM} \"$@\"\n" if name == "npm" else "exit 0\n"))
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

    def test_instructions_backup_survives_a_failed_install_and_uninstall(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            instructions = home / ".pi/agent/AGENTS.md"
            instructions.parent.mkdir(parents=True)
            instructions.write_text("user instructions\n")
            with mock.patch.object(configs, "update_mcp", side_effect=ValueError("broken mcp.json")), self.assertRaises(ValueError):
                    steps.install(home, skip_external=True, force=True)
            steps.install(home, skip_external=True, force=True)
            real_move = shutil.move

            def fail_on_instructions(source, destination):
                if Path(destination) == instructions:
                    raise OSError("move failed")
                return real_move(source, destination)

            with mock.patch.object(shutil, "move", side_effect=fail_on_instructions), self.assertRaises(OSError):
                    steps.uninstall(home, skip_external=True)
            steps.uninstall(home, skip_external=True)
            self.assertEqual(instructions.read_text(), "user instructions\n")


if __name__ == "__main__":
    unittest.main()
