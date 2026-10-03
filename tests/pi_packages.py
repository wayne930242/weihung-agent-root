"""Pi package identity, pin rotation, company plugins, and the package step."""

import json
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from pi_root import external, packages, steps
from support.pi import PINS, fake_npm_install, run_script


class PackageTests(unittest.TestCase):
    def test_package_identity_ignores_the_npm_version(self):
        agent = Path("/unused")
        self.assertEqual(packages.package_id("npm:pi-lens@4.3.0", agent), "npm:pi-lens")
        self.assertEqual(packages.package_id("npm:@scope/name@1.0.0", agent), "npm:@scope/name")
        self.assertEqual(packages.package_id("npm:@scope/name", agent), "npm:@scope/name")
        self.assertEqual(packages.package_id({"source": "npm:pi-lens", "skills": []}, agent), "npm:pi-lens")

    def test_earlier_straw_boss_revisions_are_retired_for_the_pin(self):
        for earlier in ("git:github.com/wayne930242/straw-boss", "git:github.com/wayne930242/straw-boss@old-commit"):
            with self.subTest(earlier=earlier), tempfile.TemporaryDirectory() as directory:
                home = Path(directory)
                agent = home / ".pi/agent"
                agent.mkdir(parents=True)
                (agent / "settings.json").write_text(json.dumps({"packages": [earlier]}))
                run_script("install.sh", home, "--skip-external")
                installed = json.loads((agent / "settings.json").read_text())["packages"]
                declaration = re.search(r'STRAW_BOSS_SOURCE = "([^"]+)"', PINS.read_text())
                if declaration is None:
                    self.fail("STRAW_BOSS_SOURCE is not declared in pins.py")
                self.assertEqual([item for item in installed if "straw-boss" in item], [declaration.group(1)])

    def test_retired_theme_package_is_replaced_and_restored(self):
        old = {"source": "npm:@victor-software-house/pi-curated-themes@0.2.1", "themes": ["themes/catppuccin-mocha.json"], "skills": []}
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            (agent / "settings.json").write_text(json.dumps({"packages": [old, "npm:user-package"]}))
            run_script("install.sh", home, "--skip-external")
            installed = json.loads((agent / "settings.json").read_text())["packages"]
            self.assertNotIn(old, installed)
            self.assertIn({"source": "npm:@sherif-fanous/pi-catppuccin@0.2.0", "themes": ["themes/catppuccin-mocha.json"]}, installed)
            self.assertIn("npm:user-package", installed)
            run_script("uninstall.sh", home, "--skip-external")
            self.assertEqual(json.loads((agent / "settings.json").read_text())["packages"], [old, "npm:user-package"])

    def test_merged_secret_drop_package_is_removed_and_restored(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            agent.mkdir(parents=True)
            (agent / "settings.json").write_text(json.dumps({"packages": ["npm:pi-secret-drop@0.1.6", "npm:user-package"]}))
            run_script("install.sh", home, "--skip-external")
            installed = json.loads((agent / "settings.json").read_text())["packages"]
            self.assertNotIn("npm:pi-secret-drop@0.1.6", installed)
            self.assertIn("npm:pi-robot-hand@0.2.0", installed)
            run_script("uninstall.sh", home, "--skip-external")
            self.assertEqual(json.loads((agent / "settings.json").read_text())["packages"], ["npm:pi-secret-drop@0.1.6", "npm:user-package"])

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
            state["previous_ui_settings"] = {name: value for name, value in state["previous_ui_settings"].items()
                                             if name != "enableInstallTelemetry"}
            state.pop("previous_ui_settings_present")
            marker.write_text(json.dumps(state))
            current = json.loads(settings.read_text())
            current["packages"] = ["npm:user-package", "npm:pi-lens", "npm:pi-web-access@0.31.0"]
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

    def test_external_git_switch_keeps_the_new_checkout(self):
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

            with mock.patch.object(external, "run", fake_run):
                steps.install(home, skip_external=False, force=False)
            self.assertNotIn(old, json.loads(settings.read_text())["packages"])
            self.assertNotIn(old, removals)


if __name__ == "__main__":
    unittest.main()
