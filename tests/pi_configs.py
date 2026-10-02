"""The small managed settings: mcp-adapter and pi's built-in MCP."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import hashlib

from pi_root import configs
from support.pi import ROOT, run_script


class ConfigTests(unittest.TestCase):
    def test_mcp_config_is_the_adapter_file_and_leaves_pi_mcp_json_alone(self):
        with tempfile.TemporaryDirectory() as directory:
            agent = Path(directory) / ".pi/agent"
            agent.mkdir(parents=True)
            self.assertEqual(configs.mcp_config_path(agent), agent / "mcp-adapter.json")
            (agent / "mcp.json").write_text('{"mcpServers": {"user": {}}}')
            self.assertEqual(configs.mcp_config_path(agent), agent / "mcp-adapter.json")
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

    def test_research_hub_is_registered_and_a_user_entry_is_restored(self):
        user_entry = {"command": "my-research-hub"}
        for before in (None, user_entry):
            with self.subTest(before=before), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                agent = home / ".pi/agent"
                agent.mkdir(parents=True)
                path = agent / "mcp-adapter.json"
                if before is not None:
                    path.write_text(json.dumps({"mcpServers": {"research-hub": before}}))
                run_script("install.sh", home, "--skip-external", "--force")
                server = json.loads(path.read_text())["mcpServers"]["research-hub"]
                self.assertEqual(server, configs.RESEARCH_HUB_SERVER)
                self.assertIn(configs.THESIS_TOOLKIT, server["args"])
                run_script("uninstall.sh", home, "--skip-external")
                restored = json.loads(path.read_text()).get("mcpServers", {}) if path.exists() else {}
                self.assertEqual(restored.get("research-hub"), before)



class HerdrModelsTests(unittest.TestCase):
    def setUp(self):
        self.repo_models = json.loads((ROOT / "pi/herdr-agents-models.json").read_text())

    def test_models_follow_the_repository_file_and_uninstall_restores_the_previous_value(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            config = home / ".pi/agent/herdr-agents/config.json"
            config.parent.mkdir(parents=True)
            config.write_text(json.dumps({"models": {"default": "user/model"}, "other": True}))
            run_script("install.sh", home, "--skip-external", "--force")
            self.assertEqual(json.loads(config.read_text())["models"], self.repo_models)
            run_script("install.sh", home, "--skip-external")
            self.assertEqual(json.loads(config.read_text())["models"], self.repo_models)
            run_script("uninstall.sh", home, "--skip-external")
            self.assertEqual(json.loads(config.read_text()), {"models": {"default": "user/model"}, "other": True})

    def test_a_hand_edit_since_install_stops_the_next_install(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            run_script("install.sh", home, "--skip-external")
            config = home / ".pi/agent/herdr-agents/config.json"
            edited = json.loads(config.read_text())
            edited["models"]["agents"]["reviewer"] = "user/edited"
            config.write_text(json.dumps(edited))
            failed = run_script("install.sh", home, "--skip-external", check=False)
            self.assertNotEqual(failed.returncode, 0)
            self.assertIn("herdr-agents-models.json", failed.stderr)
            self.assertEqual(json.loads(config.read_text())["models"]["agents"]["reviewer"], "user/edited")
            run_script("install.sh", home, "--skip-external", "--force")
            self.assertEqual(json.loads(config.read_text())["models"], self.repo_models)

    def test_install_retires_the_model_strategy_profile_left_by_an_earlier_install(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            run_script("install.sh", home, "--skip-external")
            roles = home / ".pi/agent/herdr-agents/roles"
            roles.mkdir()
            ours, users = roles / "coding.md", roles / "mine.md"
            ours.write_text("generated tier role\n")
            users.write_text("user role\n")
            marker = home / ".pi/agent/.weihung-agent-root.json"
            state = json.loads(marker.read_text())
            state.update({key: {} for key in configs.RETIRED_PROFILE_KEYS})
            state["installed_roles"] = {"coding.md": hashlib.sha256(ours.read_bytes()).hexdigest(),
                                        "mine.md": "not-this-file"}
            marker.write_text(json.dumps(state))
            run_script("install.sh", home, "--skip-external")
            self.assertFalse(ours.exists())
            self.assertTrue(users.exists(), "a role the installer did not write stays")
            state = json.loads(marker.read_text())
            self.assertFalse(set(configs.RETIRED_PROFILE_KEYS) & set(state), state)


class RemovedModelProfileTests(unittest.TestCase):
    """The model strategy profile was removed on 2026-10-03; models live in pi/herdr-agents-models.json."""

    def test_the_profile_does_not_come_back(self):
        for relative in ("skills/managing-model-preferences", "pi/model-profiles.json", "scripts/pi_root/profile.py",
                         "pi/extensions/tier-roles.ts"):
            self.assertFalse((ROOT / relative).exists(), relative)
        self.assertNotIn("tier-roles", (ROOT / "package.json").read_text())
        self.assertNotIn("apply-profile", (ROOT / "scripts/pi_root/cli.py").read_text())
        template = (ROOT / "pi/AGENTS.md.in").read_text()
        for word in ("managing-model-preferences", "model strategy", "tier"):
            self.assertNotIn(word, template)
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            run_script("install.sh", home, "--skip-external")
            self.assertFalse((home / ".pi/agent/herdr-agents/roles").exists())
            self.assertFalse((home / ".agents/skills/managing-model-preferences").exists())

if __name__ == "__main__":
    unittest.main()
