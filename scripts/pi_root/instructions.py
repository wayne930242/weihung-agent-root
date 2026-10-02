"""The generated ~/.pi/agent/AGENTS.md."""

import hashlib
import shutil
from datetime import datetime
from pathlib import Path

from .context import Context
from .paths import ROOT


def instructions() -> str:
    return (ROOT / "pi/AGENTS.md.in").read_text().rstrip() + "\n"


def digest(content: str) -> str:
    return hashlib.sha256(content.encode()).hexdigest()


def path(home: Path) -> Path:
    return home / ".pi/agent/AGENTS.md"


def apply(ctx: Context) -> None:
    """Write the generated file, backing up a user-owned one only with --force."""
    state = ctx.state
    target = path(ctx.home)
    content = instructions()
    current_hash = hashlib.sha256(target.read_bytes()).hexdigest() if target.exists() else None
    if current_hash and (ctx.first_install or current_hash != state.get("instructions_hash")):
        if not ctx.force:
            raise ValueError(f"{target} exists; use --force to back it up")
        backup = ctx.home / ".local/state/weihung-agent-root/backups" / datetime.now().astimezone().strftime("%Y%m%d-%H%M%S") / ".pi/agent/AGENTS.md"
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(target, backup)
        state["instructions_backup"] = str(backup)
        ctx.save()
    ctx.agent_dir.mkdir(parents=True, exist_ok=True)
    if not target.exists() or target.read_text() != content:
        target.write_text(content)
    state["instructions_hash"] = digest(content)
    # A rerun after a later failure must recognize this file as ours, not back it up over the user's.
    ctx.save()


def restore(ctx: Context) -> None:
    target = path(ctx.home)
    if target.exists() and hashlib.sha256(target.read_bytes()).hexdigest() == ctx.state.get("instructions_hash"):
        target.unlink()
    backup = ctx.state.get("instructions_backup")
    if backup and Path(backup).exists() and not target.exists():
        shutil.move(backup, target)

