"""A fresh machine has neither an aaaav checkout nor the company mp-infra plugin beside this repo."""

import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
AAAAV_GIT = "git:github.com/wayne930242/aaaav"


def write(path, content, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    if executable:
        path.chmod(0o755)


def run(script, home, env):
    return subprocess.run(["bash", str(ROOT / "scripts" / script), "--home", str(home), "--target", "pi"],
                          env=env, check=True, capture_output=True, text=True)


with tempfile.TemporaryDirectory(prefix="pi-fresh-machine-") as temporary:
    base = Path(temporary)
    home = base / "home"
    bin_dir = base / "bin"
    calls = base / "pi-calls.log"
    fixture = base / "team-toon-tack"
    write(fixture / "skills/managing-linear-tasks/SKILL.md", "---\nname: managing-linear-tasks\ndescription: Test skill\n---\n")
    write(fixture / "commands/ttt-status.md", "# ttt status\n")
    write(home / ".local/bin/codebase-memory-mcp", """#!/usr/bin/env python3
import os
from pathlib import Path
home = Path(os.environ['HOME']) / '.pi/agent'
(home / 'extensions').mkdir(parents=True, exist_ok=True)
(home / 'skills/codebase-memory').mkdir(parents=True, exist_ok=True)
(home / 'extensions/cbmem.ts').write_text("const BIN = '" + str(Path(os.environ['HOME']) / '.local/bin/codebase-memory-mcp') + "';\\n")
(home / 'skills/codebase-memory/SKILL.md').write_text('---\\nname: codebase-memory\\ndescription: Test skill\\n---\\n')
""", True)
    write(bin_dir / "npm", """#!/usr/bin/env python3
import os, shutil, sys
from pathlib import Path
args = sys.argv[1:]
if '--prefix' in args:
    prefix = Path(args[args.index('--prefix') + 1])
    shutil.copytree(os.environ['TEST_TTT_FIXTURE'], prefix / 'node_modules/team-toon-tack', dirs_exist_ok=True)
    cli = prefix / 'node_modules/.bin/ttt'
    cli.parent.mkdir(parents=True, exist_ok=True)
    cli.write_text('#!/bin/sh\\n')
    cli.chmod(0o755)
""", True)
    write(bin_dir / "pi", f"#!/bin/sh\necho \"$@\" >> '{calls}'\n", True)
    write(bin_dir / "herdr", "#!/bin/sh\nexit 0\n", True)
    env = {**os.environ, "HOME": str(home), "PATH": f"{bin_dir}:{os.environ['PATH']}",
           "PI_MP_INFRA_ROOT": str(base / "no-mp-infra"), "PI_AAAAV_ROOT": str(base / "no-aaaav"),
           "TEST_TTT_FIXTURE": str(fixture)}
    agent = home / ".pi/agent"

    result = run("install.sh", home, env)
    assert "mp-infra" in result.stderr and "skipped" in result.stderr, result.stderr
    assert not (agent / "mp-infra.json").exists()
    assert f"install {AAAAV_GIT}" in calls.read_text().splitlines()
    assert AAAAV_GIT in json.loads((agent / "settings.json").read_text())["packages"]

    run("uninstall.sh", home, env)
    assert f"remove {AAAAV_GIT}" in calls.read_text().splitlines()
    print("pi fresh machine: pass")
