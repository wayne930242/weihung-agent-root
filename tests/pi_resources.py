"""Ported resources: backups of user files and restores that fail midway."""

import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pi_root import jsonfile, paths, resources


class ResourceTests(unittest.TestCase):
    def test_backup_survives_a_failed_link_and_is_restored(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            destination = home / ".pi/agent/skills/pi-skills"
            destination.parent.mkdir(parents=True)
            destination.write_text("user copy\n")
            source = home / "clone"
            source.mkdir()
            with mock.patch.object(Path, "symlink_to", side_effect=OSError("link failed")), self.assertRaises(OSError):
                    resources.managed_resource(home, {}, destination, source, force=True, link=True)
            state = jsonfile.read_json(home / paths.MARKER)
            resources.managed_resource(home, state, destination, source, force=True, link=True)
            resources.uninstall_ported_resources(home, jsonfile.read_json(home / paths.MARKER))
            self.assertEqual(destination.read_text(), "user copy\n")

    def test_failed_restore_is_retried_by_the_next_uninstall(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            destination = home / ".pi/agent/skills/pi-skills"
            destination.parent.mkdir(parents=True)
            destination.write_text("user copy\n")
            source = home / "clone"
            source.mkdir()
            resources.managed_resource(home, {}, destination, source, force=True, link=True)
            state = jsonfile.read_json(home / paths.MARKER)
            with mock.patch.object(shutil, "move", side_effect=OSError("move failed")), self.assertRaises(OSError):
                    resources.uninstall_ported_resources(home, state)
            resources.uninstall_ported_resources(home, state)
            self.assertEqual(destination.read_text(), "user copy\n")


if __name__ == "__main__":
    unittest.main()
