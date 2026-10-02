"""The small managed settings: mcp-adapter and pi's built-in MCP."""

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pi_root import configs
from support.pi import run_script


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


if __name__ == "__main__":
    unittest.main()
