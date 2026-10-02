"""Paths, the installer scripts, and a fake npm install for the installer tests."""

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PI_TARGET = ROOT / "scripts/pi-target.py"
PINS = ROOT / "scripts/pi_root/pins.py"
FAKE_NPM = Path(__file__).resolve().with_name("fake_npm.py")


def fake_npm_install(args: list[str]) -> None:
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


def run_script(script: str, home: Path, *args: str, env: dict | None = None, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(ROOT / "scripts" / script), "--home", str(home), *args],
        env={**os.environ, "HOME": str(home), **(env or {})},
        text=True, capture_output=True, check=check,
    )
