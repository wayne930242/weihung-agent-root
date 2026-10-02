"""Files and links pi cannot install as packages: team-toon-tack and pi-skills."""

import hashlib
import shutil
from datetime import datetime
from pathlib import Path

from . import external
from .jsonfile import write_json
from .paths import MARKER, PI_SKILLS_CLONE, PI_SKILLS_GIT, TTT_PREFIX


def managed_resource(home, state, destination, source, force=False, link=False):
    """Install a file or link while retaining a user-owned predecessor."""
    key = str(destination.relative_to(home))
    records = state.setdefault("ported_resources", {})
    record = records.get(key)
    if destination.exists() or destination.is_symlink():
        current = (destination.readlink().as_posix() if destination.is_symlink() else
                   hashlib.sha256(destination.read_bytes()).hexdigest() if destination.is_file() else None)
        if record and current == record.get("installed"):
            destination.unlink()
        elif not record and ((link and destination.is_symlink() and current == str(source)) or
                             (not link and destination.is_file() and current == hashlib.sha256(source).hexdigest())):
            return
        else:
            if not force:
                raise ValueError(f"{destination} exists; use --force to back it up")
            backup = home / ".local/state/weihung-agent-root/backups" / datetime.now().astimezone().strftime("%Y%m%d-%H%M%S") / key
            backup.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(destination, backup)
            record = {**(record or {}), "backup": str(backup)}
            # Record the backup before the next step can fail, so uninstall still restores it.
            records[key] = record
            write_json(home / MARKER, state)
    destination.parent.mkdir(parents=True, exist_ok=True)
    if link:
        destination.symlink_to(source)
        installed = str(source)
    else:
        destination.write_bytes(source)
        installed = hashlib.sha256(source).hexdigest()
    records[key] = {**(record or {}), "installed": installed, "link": link}
    write_json(home / MARKER, state)


def install_ported_resources(home, state, force):
    agent_dir = home / ".pi/agent"
    prefix = home / TTT_PREFIX
    external.run(["npm", "install", "--prefix", str(prefix), "--no-save", "--no-package-lock", "team-toon-tack@latest"], home)
    ttt_root = prefix / "node_modules/team-toon-tack"
    if not (ttt_root / "skills/managing-linear-tasks/SKILL.md").is_file():
        raise ValueError(f"team-toon-tack package is missing: {ttt_root}")
    state["ttt_prefix"] = str(prefix)
    write_json(home / MARKER, state)

    managed_resource(home, state, agent_dir / "skills/managing-linear-tasks", ttt_root / "skills/managing-linear-tasks", force, link=True)
    for command in sorted((ttt_root / "commands").glob("ttt-*.md")):
        action = ("Create the resulting project skill under `.agents/skills/` for Pi."
                  if command.stem == "ttt-write-work-on-skill" else
                  f"Use Pi's shell tool and `{home / '.local/bin/ttt'}` for the matching CLI operation.")
        prompt = (f"---\ndescription: Run team-toon-tack {command.stem.removeprefix('ttt-')}\n"
                  f"argument-hint: '[arguments]'\n---\n"
                  f"Read and follow `{command}` for this request. Interpret its `{{{{ ... }}}}` placeholders "
                  "from these arguments: $ARGUMENTS. Translate `/ttt:*` references to Pi's `/ttt-*` templates. "
                  f"{action}\n")
        managed_resource(home, state, agent_dir / "prompts" / command.name, prompt.encode(), force)
    cli = prefix / "node_modules/.bin/ttt"
    if not cli.exists():
        raise ValueError(f"team-toon-tack CLI is missing: {cli}")
    managed_resource(home, state, home / ".local/bin/ttt", cli, force, link=True)
    clone = home / PI_SKILLS_CLONE
    if (clone / ".git").is_dir():
        external.run(["git", "-C", str(clone), "pull", "-q", "--ff-only"], home)
    else:
        external.run(["git", "clone", "-q", "--depth", "1", PI_SKILLS_GIT, str(clone)], home)
    state["pi_skills_clone"] = str(clone)
    write_json(home / MARKER, state)
    managed_resource(home, state, agent_dir / "skills/pi-skills", clone, force, link=True)


def restore_resource(home, key, record):
    destination = home / key
    if destination.is_symlink():
        current = destination.readlink().as_posix()
    elif destination.is_file():
        current = hashlib.sha256(destination.read_bytes()).hexdigest()
    elif destination.exists():
        return
    else:
        current = None
    # A missing destination still gets its backup back: an earlier run may have failed between the two.
    if current is not None:
        if current != record.get("installed"):
            return
        destination.unlink()
    backup = record.get("backup")
    if backup and Path(backup).exists():
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(backup, destination)


def uninstall_ported_resources(home, state):
    for key, record in reversed(list(state.get("ported_resources", {}).items())):
        restore_resource(home, key, record)
    prefix = state.get("ttt_prefix")
    if prefix and Path(prefix) == home / TTT_PREFIX and Path(prefix).exists():
        shutil.rmtree(prefix)
    clone = state.get("pi_skills_clone")
    if clone and Path(clone) == home / PI_SKILLS_CLONE and Path(clone).exists():
        shutil.rmtree(clone)
