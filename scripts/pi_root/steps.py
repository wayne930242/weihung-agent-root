"""Install and uninstall: the order the managed parts are applied in, and restored in reverse."""

from collections.abc import Callable
from pathlib import Path
from typing import NamedTuple

from . import configs, instructions, packages, profile
from .context import Context
from .jsonfile import read_json
from .paths import MARKER


class Step(NamedTuple):
    name: str
    apply: Callable[[Context], None]
    restore: Callable[[Context], None]


# Install runs these in order, saving the marker after each; uninstall restores them in reverse. The order sets the key
# order of files a fresh install creates. Restoring only reassigns or removes keys, so reverse order leaves it alone.
STEPS = (
    Step("instructions", instructions.apply, instructions.restore),
    Step("mcp-adapter", configs.apply_mcp, configs.restore_mcp),
    Step("pi-lens", configs.apply_lens, configs.restore_lens),
    Step("open-tui", configs.apply_open_tui, configs.restore_open_tui),
    Step("profile", profile.apply, profile.restore),
    Step("ui", configs.apply_ui, configs.restore_ui),
    Step("compaction", configs.apply_compaction, configs.restore_compaction),
    # Last to apply and first to restore: pi packages, the tools they need, and the resources ported beside them.
    Step("packages", packages.apply, packages.restore),
)


def install(home: Path, skip_external: bool, force: bool, herdr_root: str | None = None) -> None:
    marker = home / MARKER
    ctx = Context(home, read_json(marker), skip_external, force, herdr_root, first_install=not marker.exists())
    # Planning writes nothing, so an install that stops at its first step leaves no marker behind.
    packages.plan(ctx)
    for step in STEPS:
        step.apply(ctx)
        ctx.save()


def uninstall(home: Path, skip_external: bool) -> None:
    marker = home / MARKER
    if not marker.exists():
        return
    ctx = Context(home, read_json(marker), skip_external)
    for step in reversed(STEPS):
        step.restore(ctx)
    marker.unlink()


def apply_profile(home: Path) -> None:
    """Re-point an installed home at the active strategy without reinstalling packages."""
    marker = home / MARKER
    ctx = Context(home, read_json(marker))
    if not ctx.state:
        raise ValueError("Pi target is not installed")
    instructions.require_unchanged(ctx)
    profile.apply(ctx)
    instructions.rewrite(ctx)
    ctx.save()
