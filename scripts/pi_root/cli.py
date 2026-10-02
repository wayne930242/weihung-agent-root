"""The pi-target.py command line."""

import argparse
import hashlib
from pathlib import Path

from . import instructions, jsonfile, packages, profile, steps
from .paths import MARKER


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("migrate", "install", "uninstall", "apply-profile"))
    parser.add_argument("--home", type=Path, default=Path.home())
    parser.add_argument("--skip-external", action="store_true")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    home = args.home.expanduser().resolve()
    # install.sh runs `migrate` first, so a wrong override stops there, before any link changes a file.
    herdr_root = packages.herdr_agents_root() if args.action in ("migrate", "install") else None
    if args.action == "install":
        steps.install(home, args.skip_external, args.force, herdr_root)
    elif args.action == "uninstall":
        steps.uninstall(home, args.skip_external)
    elif args.action == "apply-profile":
        marker_path = home / MARKER
        state = jsonfile.read_json(marker_path)
        if not state:
            raise ValueError("Pi target is not installed")
        instructions_path = home / ".pi/agent/AGENTS.md"
        if hashlib.sha256(instructions_path.read_bytes()).hexdigest() != state.get("instructions_hash"):
            raise ValueError("Pi instructions changed since installation; inspect the file before applying a profile")
        profile.update_profile(home, state)
        instructions_path.write_text(instructions.instructions())
        state["instructions_hash"] = hashlib.sha256(instructions.instructions().encode()).hexdigest()
        jsonfile.write_json(marker_path, state)
