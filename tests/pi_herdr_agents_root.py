"""PI_HERDR_AGENTS_ROOT swaps the pinned pi-herdr-agents release for a local checkout, never loading both."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PINNED_SPEC = "git:github.com/wayne930242/pi-herdr-agents@1616f37ab270b22caefd8cccb1f7bc3f793e67b2"
RETIRED_NPM = "npm:pi-herdr-agents@2.0.4"
VARIABLE = "PI_HERDR_AGENTS_ROOT"


def checkout(base, name="pi-herdr-agents", package="pi-herdr-agents"):
    path = base / name
    path.mkdir(parents=True)
    (path / "package.json").write_text(json.dumps({"name": package, "version": "2.0.4"}))
    return path.resolve()


def run_script(script, home, *args, override=None, check=True, bin_dir=None):
    env = {key: value for key, value in os.environ.items() if key != VARIABLE}
    env["HOME"] = str(home)
    if override is not None:
        env[VARIABLE] = str(override)
    if bin_dir:
        env["PATH"] = f"{bin_dir}:{env['PATH']}"
    return subprocess.run(["bash", str(ROOT / "scripts" / script), "--home", str(home), *args],
                          env=env, text=True, capture_output=True, check=check)


def packages(home):
    return json.loads((home / ".pi/agent/settings.json").read_text()).get("packages", [])


def herdr_entries(home):
    return [package for package in packages(home) if "pi-herdr-agents" in (package if isinstance(package, str) else package["source"])]


def state(home):
    return json.loads((home / ".pi/agent/.weihung-agent-root.json").read_text())


def snapshot(home):
    return {str(path.relative_to(home)): path.read_text() for path in (home / ".pi/agent").rglob("*")
            if path.is_file() and not path.is_symlink()}


class HerdrAgentsRoot(unittest.TestCase):
    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.base = Path(self._directory.name)
        self.home = self.base / "home"
        self.home.mkdir()

    def install(self, override=None, *args):
        return run_script("install.sh", self.home, "--skip-external", *args, override=override)

    def test_default_pins_the_fork_commit(self):
        self.install()
        self.assertEqual(herdr_entries(self.home), [PINNED_SPEC])
        self.assertNotIn("herdr_agents", state(self.home))

    def test_empty_variable_counts_as_unset(self):
        self.install(override="")
        self.assertEqual(herdr_entries(self.home), [PINNED_SPEC])

    def test_override_replaces_the_npm_release_with_the_local_path(self):
        local = checkout(self.base)
        result = self.install(local)
        self.assertEqual(herdr_entries(self.home), [str(local)])
        self.assertEqual(state(self.home)["herdr_agents"], str(local))
        self.assertIn(str(local), result.stderr)
        self.assertIn("agents/", result.stderr)
        self.assertNotIn("herdr_agents_displaced", state(self.home))

    def test_rerun_with_the_override_changes_nothing(self):
        local = checkout(self.base)
        self.install(local)
        first = snapshot(self.home)
        self.install(local)
        self.assertEqual(snapshot(self.home), first)

    def test_switching_from_the_pin_to_local_removes_the_pinned_entry(self):
        local = checkout(self.base)
        self.install()
        self.assertEqual(herdr_entries(self.home), [PINNED_SPEC])
        self.install(local)
        self.assertEqual(herdr_entries(self.home), [str(local)])

    def test_unsetting_the_override_restores_the_pin_without_a_duplicate(self):
        local = checkout(self.base)
        self.install(local)
        self.install()
        self.assertEqual(herdr_entries(self.home), [PINNED_SPEC])
        self.assertNotIn("herdr_agents", state(self.home))
        self.assertNotIn("herdr_agents_displaced", state(self.home))

    def test_moving_the_override_to_another_checkout_drops_the_old_path(self):
        first, second = checkout(self.base, "one/pi-herdr-agents"), checkout(self.base, "two/pi-herdr-agents")
        self.install(first)
        self.install(second)
        self.assertEqual(herdr_entries(self.home), [str(second)])

    def test_a_relative_override_is_stored_absolute(self):
        local = checkout(self.base)
        subprocess.run(["bash", str(ROOT / "scripts/install.sh"), "--home", str(self.home), "--skip-external"],
                       env={**{k: v for k, v in os.environ.items() if k != VARIABLE}, "HOME": str(self.home), VARIABLE: "pi-herdr-agents"},
                       cwd=self.base, check=True, capture_output=True, text=True)
        self.assertEqual(herdr_entries(self.home), [str(local)])

    def test_missing_directory_fails_before_writing_anything(self):
        result = run_script("install.sh", self.home, "--skip-external", override=self.base / "absent", check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn(VARIABLE, result.stderr)
        self.assertIn("absent", result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_wrong_package_fails_before_writing_anything(self):
        other = checkout(self.base, "other", package="something-else")
        result = run_script("install.sh", self.home, "--skip-external", override=other, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("something-else", result.stderr)
        self.assertEqual(list(self.home.iterdir()), [])

    def test_directory_without_package_json_fails(self):
        empty = self.base / "empty"
        empty.mkdir()
        result = run_script("install.sh", self.home, "--skip-external", override=empty, check=False)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("package.json", result.stderr)

    def test_failed_override_leaves_an_existing_install_untouched(self):
        self.install()
        first = snapshot(self.home)
        run_script("install.sh", self.home, "--skip-external", override=self.base / "absent", check=False)
        self.assertEqual(snapshot(self.home), first)

    def test_uninstall_removes_the_local_entry(self):
        local = checkout(self.base)
        self.install(local)
        run_script("uninstall.sh", self.home, "--skip-external")
        self.assertFalse((self.home / ".pi/agent/.weihung-agent-root.json").exists())
        self.assertEqual(herdr_entries(self.home), [])

    def test_install_retires_the_npm_release_so_only_the_fork_pin_loads(self):
        agent = self.home / ".pi/agent"
        agent.mkdir(parents=True)
        (agent / "settings.json").write_text(json.dumps({"packages": [RETIRED_NPM]}))
        self.install()
        self.assertEqual(herdr_entries(self.home), [PINNED_SPEC])
        self.install()
        self.assertEqual(herdr_entries(self.home), [PINNED_SPEC])
        run_script("uninstall.sh", self.home, "--skip-external")
        self.assertEqual(herdr_entries(self.home), [RETIRED_NPM])

    def test_uninstall_restores_a_prior_npm_spec_the_override_displaced(self):
        agent = self.home / ".pi/agent"
        agent.mkdir(parents=True)
        (agent / "settings.json").write_text(json.dumps({"packages": ["npm:pi-herdr-agents@2.0.1"]}))
        local = checkout(self.base)
        self.install(local)
        self.assertEqual(herdr_entries(self.home), [str(local)])
        run_script("uninstall.sh", self.home, "--skip-external")
        self.assertEqual(herdr_entries(self.home), ["npm:pi-herdr-agents@2.0.1"])

    def test_uninstall_after_unsetting_restores_the_prior_spec_like_before(self):
        agent = self.home / ".pi/agent"
        agent.mkdir(parents=True)
        (agent / "settings.json").write_text(json.dumps({"packages": ["npm:pi-herdr-agents@2.0.1"]}))
        local = checkout(self.base)
        self.install(local)
        self.install()
        run_script("uninstall.sh", self.home, "--skip-external")
        self.assertEqual(herdr_entries(self.home), ["npm:pi-herdr-agents@2.0.1"])


class ExternalInstall(unittest.TestCase):
    """The pi commands the installer runs, with stub npm, pi, and herdr."""

    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        self.addCleanup(self._directory.cleanup)
        self.base = Path(self._directory.name)
        self.home = self.base / "home"
        self.home.mkdir()
        self.calls = self.base / "pi-calls.log"
        bin_dir = self.bin_dir = self.base / "bin"
        bin_dir.mkdir()
        fixture = self.base / "team-toon-tack"
        (fixture / "skills/managing-linear-tasks").mkdir(parents=True)
        (fixture / "skills/managing-linear-tasks/SKILL.md").write_text("---\nname: managing-linear-tasks\n---\n")
        (fixture / "commands").mkdir()
        (fixture / "commands/ttt-status.md").write_text("# ttt status\n")
        self.write(bin_dir / "npm", f"""#!/usr/bin/env python3
import shutil, sys
from pathlib import Path
args = sys.argv[1:]
if args[:1] == ['ls']:
    sys.exit(1)
if '--prefix' in args:
    prefix = Path(args[args.index('--prefix') + 1])
    shutil.copytree('{fixture}', prefix / 'node_modules/team-toon-tack', dirs_exist_ok=True)
    cli = prefix / 'node_modules/.bin/ttt'
    cli.parent.mkdir(parents=True, exist_ok=True)
    cli.write_text('#!/bin/sh\\n')
    cli.chmod(0o755)
""")
        pi_skills = self.base / "pi-skills"
        (pi_skills / "brave-search").mkdir(parents=True)
        (pi_skills / "brave-search/SKILL.md").write_text("---\nname: brave-search\n---\n")
        for command in (["init", "-q"], ["add", "."], ["-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "fixture"]):
            subprocess.run(["git", "-C", str(pi_skills), *command] if command[0] != "init" else ["git", "init", "-q", str(pi_skills)],
                           check=True, capture_output=True)
        self.write(bin_dir / "pi", f"#!/bin/sh\necho \"$@\" >> '{self.calls}'\n")
        self.write(bin_dir / "herdr", "#!/bin/sh\nexit 0\n")
        self.env = {"PI_SKILLS_GIT": str(pi_skills), "PI_MP_INFRA_ROOT": str(self.base / "no-mp-infra"),
                    "PI_SDLC_ROOT": str(self.base / "no-sdlc"), "PI_AAAAV_ROOT": str(self.base / "no-aaaav")}

    @staticmethod
    def write(path, content):
        path.write_text(content)
        path.chmod(0o755)

    def run_install(self, override=None):
        env = {key: value for key, value in os.environ.items() if key != VARIABLE}
        env.update(self.env, HOME=str(self.home), PATH=f"{self.bin_dir}:{env['PATH']}")
        if override:
            env[VARIABLE] = str(override)
        return subprocess.run(["bash", str(ROOT / "scripts/install.sh"), "--home", str(self.home)],
                              env=env, text=True, capture_output=True, check=True)

    def pi_calls(self):
        return self.calls.read_text().splitlines()

    def test_override_installs_the_path_not_the_npm_release_and_removes_a_recorded_npm_entry(self):
        local = checkout(self.base)
        self.run_install()
        self.assertIn(f"install {PINNED_SPEC}", self.pi_calls())
        self.calls.write_text("")
        self.run_install(local)
        calls = self.pi_calls()
        self.assertIn(f"install {local}", calls)
        self.assertNotIn(f"install {PINNED_SPEC}", calls)
        self.assertIn(f"remove {PINNED_SPEC}", calls)
        self.assertEqual(herdr_entries(self.home), [str(local)])

    def test_unsetting_the_override_removes_the_local_entry_and_reinstalls_the_npm_pin(self):
        local = checkout(self.base)
        self.run_install(local)
        self.calls.write_text("")
        self.run_install()
        calls = self.pi_calls()
        self.assertIn(f"install {PINNED_SPEC}", calls)
        self.assertIn(f"remove {local}", calls)
        self.assertEqual(herdr_entries(self.home), [PINNED_SPEC])

    def test_uninstall_removes_the_local_package_through_pi(self):
        local = checkout(self.base)
        self.run_install(local)
        self.calls.write_text("")
        env = {key: value for key, value in os.environ.items() if key != VARIABLE}
        env.update(self.env, HOME=str(self.home), PATH=f"{self.bin_dir}:{env['PATH']}")
        subprocess.run(["bash", str(ROOT / "scripts/uninstall.sh"), "--home", str(self.home)],
                       env=env, text=True, capture_output=True, check=True)
        self.assertIn(f"remove {local}", self.pi_calls())
        self.assertNotIn(f"remove {PINNED_SPEC}", self.pi_calls())
        self.assertEqual(herdr_entries(self.home), [])


if __name__ == "__main__":
    unittest.main()
