"""Commands run outside this process: npm, pi, herdr, git."""

import os
import subprocess
import sys
from pathlib import Path


def environment(home: Path) -> dict[str, str]:
    env = os.environ.copy()
    env["HOME"] = str(home)
    env["PI_CODING_AGENT_DIR"] = str(home / ".pi/agent")
    return env


def run(args: list[str], home: Path) -> None:
    subprocess.run(args, check=True, env=environment(home))


def capture(args: list[str], home: Path) -> str:
    """The stdout of a command that reports state; a failed call reports nothing."""
    result = subprocess.run(args, capture_output=True, text=True, check=False, env=environment(home))
    return result.stdout


def run_company_plugin(action: str, home: Path, source: str) -> None:
    # An optional plugin must not stop the install or uninstall: a failed `pi` call leaves its settings entry to the write that follows.
    try:
        run(["pi", action, source], home)
    except (subprocess.CalledProcessError, OSError) as error:
        print(f"could not run pi {action} for {source}: {error}; continuing.", file=sys.stderr)
