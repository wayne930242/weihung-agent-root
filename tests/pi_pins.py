"""Checks for the pin listing and bump command."""

import importlib.util
import io
import shutil
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


if __name__ == "__main__":
    unittest.main()
