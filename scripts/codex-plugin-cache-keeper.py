#!/usr/bin/env python3
"""Keep removed Codex plugin cache versions resolvable for running sessions.

Codex resolves a plugin's hook commands against its versioned cache directory
(~/.codex/plugins/cache/<marketplace>/<plugin>/<version>) when a session
starts. Upgrading the plugin deletes the previous version directory, so every
session started before the upgrade fails each hook call from then on.

Each run records every version name seen per plugin. A recorded version that
has disappeared becomes a symlink to the newest real version directory of the
same plugin. Only versions older than that newest real directory are linked:
a missing version at or above it is a reinstall in progress, and a link there
would redirect the installer's own writes.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path


def version_key(name: str) -> tuple[int, ...] | None:
    """Numeric release components, or None for a name with no version order."""
    if not re.fullmatch(r"v?\d+(\.\d+)*([-+].*)?", name):
        return None
    return tuple(int(p) for p in re.findall(r"\d+", name.split("-")[0].split("+")[0]))


def plugin_dirs(cache_root: Path):
    for marketplace in sorted(p for p in cache_root.iterdir() if p.is_dir() and not p.is_symlink()):
        for plugin in sorted(p for p in marketplace.iterdir() if p.is_dir() and not p.is_symlink()):
            yield f"{marketplace.name}/{plugin.name}", plugin


def reconcile(cache_root: Path, seen: dict[str, list[str]]) -> list[str]:
    actions: list[str] = []
    live_plugins: set[str] = set()

    for key, plugin in plugin_dirs(cache_root):
        live_plugins.add(key)
        entries = list(plugin.iterdir())
        real = [e for e in entries if e.is_dir() and not e.is_symlink()]
        names = set(seen.get(key, [])) | {e.name for e in entries}

        if real:
            ordered = [e for e in real if version_key(e.name) is not None]
            newest = max(ordered, key=lambda e: version_key(e.name)) if ordered else None
            for name in sorted(names):
                target = plugin / name
                if newest is None or target.exists() or version_key(name) is None:
                    continue
                if version_key(name) >= version_key(newest.name):
                    continue
                if target.is_symlink():
                    target.unlink()
                target.symlink_to(newest.name)
                actions.append(f"linked {key}/{name} -> {newest.name}")

        seen[key] = sorted(names)

    for key in list(seen):
        if key not in live_plugins:
            del seen[key]
    return actions


def main() -> int:
    home = Path.home()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--cache-root", type=Path, default=home / ".codex/plugins/cache")
    parser.add_argument(
        "--state",
        type=Path,
        default=home / ".codex/state/weihung-user-claude/plugin-cache-keeper.json",
    )
    args = parser.parse_args()

    if not args.cache_root.is_dir():
        return 0

    seen = json.loads(args.state.read_text()) if args.state.exists() else {}
    for action in reconcile(args.cache_root, seen):
        print(action, flush=True)

    args.state.parent.mkdir(parents=True, exist_ok=True)
    tmp = args.state.with_suffix(".tmp")
    tmp.write_text(json.dumps(seen, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, args.state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
