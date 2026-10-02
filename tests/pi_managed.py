"""The managed-value mechanism: record a value's previous state once and restore it while it is unchanged."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pi_root.managed import (
    record_keys,
    remember_keys,
    restore_keys,
    restore_nested,
    restore_value,
)


class ManagedTests(unittest.TestCase):
    def test_keys_round_trip_to_their_previous_values_and_absence(self):
        state: dict = {}
        settings = {"theme": "light", "editorPaddingX": None}
        remember_keys(state, "ui", settings, ("theme", "editorPaddingX", "collapseChangelog"))
        settings.update(theme="dark", editorPaddingX=1, collapseChangelog=True)
        record_keys(state, "ui", settings, ("theme", "editorPaddingX", "collapseChangelog"))
        restore_keys(state, "ui", settings, ("theme", "editorPaddingX", "collapseChangelog"))
        self.assertEqual(settings, {"theme": "light", "editorPaddingX": None})

    def test_a_value_the_user_changed_after_install_stays(self):
        state: dict = {}
        settings = {"theme": "light"}
        remember_keys(state, "ui", settings, ("theme",))
        settings["theme"] = "dark"
        record_keys(state, "ui", settings, ("theme",))
        settings["theme"] = "user-choice"
        restore_keys(state, "ui", settings, ("theme",))
        self.assertEqual(settings, {"theme": "user-choice"})

    def test_a_key_managed_by_a_later_version_is_remembered_on_the_next_install(self):
        state: dict = {}
        remember_keys(state, "ui", {"theme": "light"}, ("theme",))
        remember_keys(state, "ui", {"theme": "dark", "telemetry": True}, ("theme", "telemetry"))
        # The earlier value of a key managed already is kept; the new key records what it held at this install.
        self.assertEqual(state["previous_ui"], {"theme": "light", "telemetry": True})
        self.assertEqual(state["previous_ui_present"], ["theme", "telemetry"])

    def test_a_marker_without_the_present_list_counts_a_null_previous_value_as_absent(self):
        state = {"previous_ui": {"theme": None, "editorPaddingX": 2}, "installed_ui": {"theme": "dark", "editorPaddingX": 1}}
        settings = {"theme": "dark", "editorPaddingX": 1}
        restore_keys(state, "ui", settings, ("theme", "editorPaddingX"))
        self.assertEqual(settings, {"editorPaddingX": 2})

    def test_nested_keys_restore_and_an_emptied_object_is_removed(self):
        settings = {"terminal": {"showTerminalProgress": True, "showImages": False}, "panes": {"mode": "split"}}
        restore_nested(settings, "terminal", {"showTerminalProgress": True}, {}, ("showTerminalProgress",))
        restore_nested(settings, "panes", {"mode": "split"}, None, ("mode",))
        self.assertEqual(settings, {"terminal": {"showImages": False}})

    def test_a_whole_value_returns_or_leaves(self):
        config = {"models": {"default": "ours"}, "status": {"enabled": True}, "other": {"user": True}}
        restore_value(config, "models", {"default": "ours"}, {"default": "theirs"})
        restore_value(config, "status", {"enabled": True}, None)
        restore_value(config, "other", {"user": False}, None)
        self.assertEqual(config, {"models": {"default": "theirs"}, "other": {"user": True}})


if __name__ == "__main__":
    unittest.main()
