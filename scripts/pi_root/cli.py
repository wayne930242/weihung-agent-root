"""The pi-target.py command line."""

import argparse
from pathlib import Path

from . import packages, steps


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("migrate", "install", "uninstall"))
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
