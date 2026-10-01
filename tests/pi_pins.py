"""Checks for the pin listing and bump command."""

import importlib.util
import io
import json
import plistlib
import shutil
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import ModuleType
from typing import Any
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
LATEST = {"pi-lens": "9.9.9", "playwriter": "8.8.8", "github.com/wayne930242/straw-boss": "f" * 40}


def load_pins() -> ModuleType:
    spec = importlib.util.spec_from_file_location("pi_pins", ROOT / "scripts/pi-pins.py")
    if spec is None or spec.loader is None:
        raise ValueError("cannot load scripts/pi-pins.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


pins = load_pins()


def fake_latest(pin: Any) -> str:
    return LATEST.get(pin.name) or pin.current


class PinTests(unittest.TestCase):
    def test_collects_npm_git_and_playwriter_pins(self) -> None:
        collected = {pin.name: pin for pin in pins.collect_pins()}
        self.assertEqual(collected["pi-lens"].kind, "npm")
        self.assertEqual(collected["@juicesharp/rpiv-todo"].prefix, "npm:@juicesharp/rpiv-todo")
        self.assertEqual(collected["github.com/wayne930242/straw-boss"].kind, "git")
        self.assertEqual(collected["playwriter"].prefix, "playwriter")

    def test_outdated_reports_only_differing_pins(self) -> None:
        output = io.StringIO()
        with mock.patch.object(pins, "latest", fake_latest), redirect_stdout(output):
            pins.outdated()
        rows = {line.split()[0]: line for line in output.getvalue().splitlines() if line and not line.startswith(" ")}
        self.assertIn("differs", rows["pi-lens"])
        self.assertIn(" ok", rows["pi-intercom"])
        self.assertIn("3 of", output.getvalue())

    def test_bump_rewrites_npm_pins_in_every_quoting_file_and_skips_git(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            copies = []
            for path in pins.QUOTING_FILES:
                copy = Path(tmp) / str(path.relative_to(ROOT)).replace("/", "__")
                shutil.copy(path, copy)
                copies.append((path, copy))
            with mock.patch.object(pins, "latest", fake_latest), \
                    mock.patch.object(pins, "QUOTING_FILES", tuple(copy for _, copy in copies)), \
                    redirect_stdout(io.StringIO()):
                pins.bump([])
            text = {original.name: copy.read_text() for original, copy in copies}
            self.assertIn("npm:pi-lens@9.9.9", text["pi-target.py"])
            self.assertNotIn("npm:pi-lens@4.3.0", text["install.sh"])
            self.assertIn("playwriter@8.8.8", text["README.md"])
            self.assertIn("straw-boss@d48d6a5b", text["pi-target.py"])

    def test_bump_updates_a_named_git_pin(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "pi-target.py"
            shutil.copy(pins.TARGET, copy)
            with mock.patch.object(pins, "latest", fake_latest), \
                    mock.patch.object(pins, "QUOTING_FILES", (copy,)), \
                    redirect_stdout(io.StringIO()):
                pins.bump(["github.com/wayne930242/straw-boss"])
            self.assertIn("straw-boss@" + "f" * 40, copy.read_text())
            self.assertIn("npm:pi-lens@4.3.0", copy.read_text())

    def test_bump_rejects_an_unpinned_name(self) -> None:
        with self.assertRaisesRegex(ValueError, "not a pinned package"):
            pins.bump(["no-such-package"])

    def test_failed_lookup_fails_fast(self) -> None:
        failed = mock.Mock(returncode=1, stdout="", stderr="404")
        with mock.patch.object(pins.subprocess, "run", return_value=failed), self.assertRaisesRegex(ValueError, "404"):
            pins.latest(pins.Pin("npm", "npm:pi-lens", "4.3.0"))


class AutoUpdateTests(unittest.TestCase):
    NEWEST = {"pi-lens": "9.9.9", "playwriter": "8.8.8", "pi-herdr-agents": "9.0.0"}

    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.repo = Path(tmp.name) / "repo"
        (self.repo / "scripts").mkdir(parents=True)
        shutil.copy(ROOT / "scripts/pi-target.py", self.repo / "scripts/pi-target.py")
        shutil.copy(ROOT / "README.md", self.repo / "README.md")
        for command in (["init", "-q", "-b", "main"], ["config", "user.email", "t@example.com"], ["config", "user.name", "t"],
                        ["add", "."], ["commit", "-q", "-m", "base"]):
            subprocess.run(["git", "-C", str(self.repo), *command], check=True)
        self.state = Path(tmp.name) / "state"
        self.calls: list[tuple[str, str]] = []
        self.messages: list[str] = []
        self.rejected_install = ""
        self.smokes = 0
        target = self.repo / "scripts/pi-target.py"
        for name, value in {"ROOT": self.repo, "TARGET": target, "QUOTING_FILES": (target, self.repo / "README.md"),
                            "STATE_DIR": self.state, "STATE_FILE": self.state / "state.json"}.items():
            patcher = mock.patch.object(pins, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        for name, value in {"latest": lambda pin: self.NEWEST.get(pin.name) or pin.current, "step": self.fake_step,
                            "smoke": self.fake_smoke, "notify": self.messages.append,
                            "test_commands": lambda: [["bash", "tests/green.sh"], ["bash", "tests/already-red.sh"]]}.items():
            patcher = mock.patch.object(pins, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def fake_step(self, name: str, command: list[str], cwd: Path | None = None) -> None:
        self.calls.append((name, command[-1]))
        if command[-1].endswith("already-red.sh"):
            raise pins.StepFailed("red before any bump")
        if name == "install" and self.rejected_install and self.rejected_install in (self.repo / "scripts/pi-target.py").read_text():
            raise pins.StepFailed("install failed: boom")

    def fake_smoke(self) -> None:
        self.smokes += 1

    def commits(self) -> list[str]:
        return subprocess.run(["git", "-C", str(self.repo), "log", "--format=%s"], capture_output=True, text=True, check=True).stdout.splitlines()

    def auto(self) -> None:
        with redirect_stdout(io.StringIO()):
            pins.auto()

    def test_commits_one_bump_when_everything_passes_and_leaves_manual_pins(self) -> None:
        self.auto()
        self.assertEqual(self.commits()[0], "chore(pi): bump pinned packages")
        text = (self.repo / "scripts/pi-target.py").read_text()
        self.assertIn("npm:pi-lens@9.9.9", text)
        self.assertIn("npm:pi-herdr-agents@2.0.4", text)
        self.assertEqual(self.calls.count(("install", str(self.repo / "scripts/install.sh"))), 1)
        self.assertEqual(self.smokes, 1)
        self.assertEqual(self.calls.count(("tests", "tests/already-red.sh")), 1, "the red file runs only as the baseline")
        self.assertRegex(self.messages[0], r"Updated 2: .*1 test file\(s\) were already failing")

    def test_isolates_a_failing_pin_restores_it_and_remembers_the_rejection(self) -> None:
        self.rejected_install = "pi-lens@9.9.9"
        self.auto()
        self.assertEqual(self.commits()[:2], ["chore(pi): bump playwriter to 8.8.8", "base"])
        text = (self.repo / "scripts/pi-target.py").read_text()
        self.assertIn("npm:pi-lens@4.3.0", text)
        self.assertIn("playwriter@8.8.8", text)
        self.assertEqual(json.loads((self.state / "state.json").read_text())["rejected"], {"pi-lens": "9.9.9"})
        installs = [call for call in self.calls if call[0] in ("install", "restore install")]
        self.assertEqual([name for name, _ in installs], ["install", "restore install", "install", "restore install", "install"])
        self.assertEqual(subprocess.run(["git", "-C", str(self.repo), "status", "--porcelain"], capture_output=True, text=True).stdout, "")
        self.assertIn("Rejected: pi-lens@9.9.9", self.messages[0])
        self.calls.clear()
        self.messages.clear()
        self.auto()
        self.assertEqual((self.commits()[0], self.calls, self.messages), ("chore(pi): bump playwriter to 8.8.8", [], []), "a rejected version is not retried")

    def test_skips_a_dirty_tree_and_a_branch_other_than_main(self) -> None:
        (self.repo / "README.md").write_text("edited\n")
        self.auto()
        self.assertEqual(self.messages, ["Skipped: the working tree has uncommitted changes."])
        subprocess.run(["git", "-C", str(self.repo), "checkout", "-q", "--", "README.md"], check=True)
        subprocess.run(["git", "-C", str(self.repo), "checkout", "-q", "-b", "topic"], check=True)
        self.messages.clear()
        self.auto()
        self.assertEqual(self.messages, ["Skipped: the checkout is on topic, not main."])
        self.assertEqual(self.calls, [])

    def test_a_failed_restore_aborts_instead_of_reporting_success(self) -> None:
        self.rejected_install = "pi-lens@9.9.9"
        installs = iter([True, False])
        original = self.fake_step

        def failing_restore(name: str, command: list[str], cwd: Path | None = None) -> None:
            if name == "restore install" and next(installs) is False:
                raise pins.StepFailed("restore install failed")
            original(name, command, cwd)

        with mock.patch.object(pins, "step", failing_restore), self.assertRaises(pins.RestoreFailed):
            self.auto()


class SmokeAndScheduleTests(unittest.TestCase):
    def run_smoke(self, returncode: int, stdout: str) -> None:
        done = subprocess.CompletedProcess([], returncode, stdout=stdout, stderr="Error: Failed to load extension")
        with tempfile.TemporaryDirectory() as tmp, mock.patch.object(pins, "STATE_DIR", Path(tmp)), \
                mock.patch.object(pins.subprocess, "run", return_value=done):
            pins.smoke()

    def test_smoke_passes_on_a_command_list_and_fails_on_a_load_error(self) -> None:
        reply = json.dumps({"type": "response", "success": True, "data": {"commands": [{"name": "todos"}]}})
        self.run_smoke(0, "{\"type\":\"extension_ui_request\"}\n" + reply + "\n")
        with self.assertRaisesRegex(pins.StepFailed, "exited 1"):
            self.run_smoke(1, "")
        with self.assertRaisesRegex(pins.StepFailed, "no command list"):
            self.run_smoke(0, "{\"type\":\"extension_ui_request\"}\n")

    def test_a_crashed_run_notifies_and_still_fails(self) -> None:
        messages: list[str] = []
        with mock.patch.object(pins, "auto", side_effect=pins.RestoreFailed("restore install failed: x\ndetail")), \
                mock.patch.object(pins, "notify", messages.append), mock.patch.object(pins.sys, "argv", ["pi-pins.py", "auto"]), \
                self.assertRaises(pins.RestoreFailed):
            pins.main()
        self.assertRegex(messages[0], r"^Crashed: restore install failed: x See ")

    def test_plist_runs_auto_daily_with_the_tool_directories_on_path(self) -> None:
        located = {"pi": "/nvm/bin/pi", "npm": "/nvm/bin/npm", "node": "/nvm/bin/node", "git": "/usr/bin/git",
                   "python3": "/opt/homebrew/bin/python3", "bash": "/bin/bash", "herdr": "/Users/x/.local/bin/herdr"}
        with mock.patch.object(pins.shutil, "which", located.get):
            plist = plistlib.loads(plistlib.dumps(pins.launchd_plist()))
        self.assertEqual(plist["ProgramArguments"][1:], [str(ROOT / "scripts/pi-pins.py"), "auto"])
        self.assertEqual(plist["StartCalendarInterval"], {"Hour": 6, "Minute": 0})
        self.assertEqual(plist["EnvironmentVariables"]["PATH"],
                         "/opt/homebrew/bin:/nvm/bin:/usr/bin:/bin:/Users/x/.local/bin:/usr/sbin:/sbin")
        with mock.patch.object(pins.shutil, "which", {"python3": "/opt/homebrew/bin/python3", "pi": "/nvm/bin/pi"}.get), \
                self.assertRaisesRegex(ValueError, "npm is not on PATH"):
            pins.launchd_plist()


if __name__ == "__main__":
    unittest.main()
