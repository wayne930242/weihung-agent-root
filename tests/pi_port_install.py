"""Exercise the Pi plugin port through the public installer with isolated tools."""

import hashlib
import json
import os
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
COMMANDS = ("assign", "cancel", "comment", "create", "done", "edit", "estimate", "show", "status", "sync", "work-on", "write-work-on-skill")
SKILLS = ("ansible", "canary-service-discovery", "customer-host-lifecycle", "deployment", "infra-owner", "infrastructure-planning", "keycloak-management", "monitoring", "nomad", "proxy-jump-troubleshoot", "rotate-token", "tailscale-acl", "troubleshoot", "vault-security")


def write(path, content, executable=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    if executable:
        path.chmod(0o755)


def run(script, home, env, *args):
    subprocess.run(["bash", str(ROOT / "scripts" / script), "--home", str(home), "--target", "pi", *args],
                   env=env, check=True, capture_output=True, text=True)


def snapshot(agent):
    result = {}
    for path in agent.rglob("*"):
        if path.is_file() or path.is_symlink():
            relative = str(path.relative_to(agent))
            result[relative] = ("link", str(path.readlink())) if path.is_symlink() else ("file", hashlib.sha256(path.read_bytes()).hexdigest())
    return result


with tempfile.TemporaryDirectory(prefix="pi-port-install-") as temporary:
    base = Path(temporary)
    home = base / "home"
    bin_dir = base / "bin"
    plugin = base / "mp-infra"
    fixture = base / "team-toon-tack"
    for name in SKILLS:
        write(plugin / "skills" / name / "SKILL.md", f"---\nname: {name}\ndescription: Test skill\n---\n")
    write(plugin / "hooks/production-safety-hook", "#!/usr/bin/env python3\n")
    write(fixture / "skills/managing-linear-tasks/SKILL.md", "---\nname: managing-linear-tasks\ndescription: Test skill\n---\n")
    for name in COMMANDS:
        write(fixture / "commands" / f"ttt-{name}.md", f"# ttt {name}\n")
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
import os, sys, shutil
from pathlib import Path
args = sys.argv[1:]
if '--prefix' in args:
    prefix = Path(args[args.index('--prefix') + 1])
    root = prefix / 'node_modules/team-toon-tack'
    shutil.copytree(os.environ['TEST_TTT_FIXTURE'], root, dirs_exist_ok=True)
    if os.environ.get('TEST_NO_TTT_CLI') != '1':
        target = prefix / 'node_modules/.bin/ttt'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('#!/bin/sh\\necho ttt\\n')
        target.chmod(0o755)
""", True)
    write(bin_dir / "pi", "#!/bin/sh\nexit 0\n", True)
    write(bin_dir / "herdr", "#!/bin/sh\nexit 0\n", True)
    env = {**os.environ, "HOME": str(home), "PATH": f"{bin_dir}:{os.environ['PATH']}",
           "PI_MP_INFRA_ROOT": str(plugin), "TEST_TTT_FIXTURE": str(fixture)}
    agent = home / ".pi/agent"
    write(agent / "prompts/ttt-status.md", "user prompt\n")
    write(agent / "skills/infra-owner/SKILL.md", "user skill\n")
    write(agent / "extensions/moshi-hooks.ts", "user extension\n")
    failed = subprocess.run(["bash", str(ROOT / "scripts/install.sh"), "--home", str(home), "--target", "pi", "--force"],
                            env={**env, "TEST_NO_TTT_CLI": "1"}, capture_output=True, text=True)
    assert failed.returncode != 0 and "CLI is missing" in failed.stderr
    assert json.loads((agent / ".weihung-user-claude.json").read_text())["ported_resources"]
    run("install.sh", home, env)
    assert len(list((agent / "skills").iterdir())) == len(SKILLS) + 2
    assert len(list((agent / "prompts").glob("ttt-*.md"))) == 12
    assert str(home / ".local/bin/ttt") in (agent / "prompts/ttt-show.md").read_text()
    assert "`.agents/skills/`" in (agent / "prompts/ttt-write-work-on-skill.md").read_text()
    assert str(home / ".local/bin/codebase-memory-mcp") in (agent / "extensions/cbmem.ts").read_text()
    assert "pi-cbmem-" not in (agent / "extensions/cbmem.ts").read_text()
    assert (home / ".local/bin/ttt").is_symlink()
    assert (agent / "extensions/moshi-hooks.ts").read_text() == "user extension\n"
    first = snapshot(agent)
    run("install.sh", home, env)
    assert snapshot(agent) == first
    run("uninstall.sh", home, env)
    assert (agent / "prompts/ttt-status.md").read_text() == "user prompt\n"
    assert (agent / "skills/infra-owner/SKILL.md").read_text() == "user skill\n"
    assert not (agent / "extensions/cbmem.ts").exists()
    assert not (home / ".local/bin/ttt").exists()
    assert (agent / "extensions/moshi-hooks.ts").read_text() == "user extension\n"
    print("pi port install: pass")
