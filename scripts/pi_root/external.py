"""Commands run outside this process: npm, pi, herdr, git."""

import os
import subprocess
import sys
from pathlib import Path


def run(args: list[str], home: Path) -> None:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PI_CODING_AGENT_DIR"] = str(home / ".pi/agent")
    subprocess.run(args, check=True, env=env)


def run_company_plugin(action: str, home: Path, source: str) -> None:
    # An optional plugin must not stop the install or uninstall: a failed `pi` call leaves its settings entry to the write that follows.
    try:
        run(["pi", action, source], home)
    except (subprocess.CalledProcessError, OSError) as error:
        print(f"could not run pi {action} for {source}: {error}; continuing.", file=sys.stderr)
