#!/usr/bin/env python3
"""List and bump the exact versions pinned in pi-target.py."""

import argparse
import importlib.util
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "scripts/pi-target.py"
# Files that quote a pin verbatim and must move with it.
QUOTING_FILES = (TARGET, ROOT / "README.md", *sorted((ROOT / "tests").glob("*.py")),
                 *sorted((ROOT / "tests").glob("*.sh")), *sorted((ROOT / "tests").glob("*.mjs")))
NPM_PIN = re.compile(r"^(npm:(?:@[^/@]+/)?[^/@]+)@(.+)$")
GIT_PIN = re.compile(r"^(git:[^@]+)@([0-9a-f]{7,40})$")
PLAIN_NPM_PIN = re.compile(r"^([^/@:]+)@(.+)$")


class Pin(NamedTuple):
    kind: str  # "npm" or "git"
    prefix: str  # the text before "@<version>" exactly as the source files quote it
    current: str

    @property
    def name(self) -> str:
        return self.prefix.removeprefix("npm:").removeprefix("git:")


def load_target():
    spec = importlib.util.spec_from_file_location("pi_target", TARGET)
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load {TARGET}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_pins() -> list[Pin]:
    target = load_target()
    pins = []
    for value in target.PACKAGES:
        source = target.package_source(value)
        if match := NPM_PIN.match(source):
            pins.append(Pin("npm", match[1], match[2]))
        elif match := GIT_PIN.match(source):
            pins.append(Pin("git", match[1], match[2]))
    if match := PLAIN_NPM_PIN.match(target.PLAYWRITER):
        pins.append(Pin("npm", match[1], match[2]))
    return pins


def run(command: list[str]) -> str:
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        raise ValueError(f"{' '.join(command)} failed: {result.stderr.strip()}")
    return result.stdout.strip()


def latest(pin: Pin) -> str:
    if pin.kind == "npm":
        return run(["npm", "view", pin.name, "version"])
    heads = run(["git", "ls-remote", f"https://{pin.name}", "HEAD"])
    if not heads:
        raise ValueError(f"{pin.name} has no HEAD")
    return heads.split()[0]


def latest_all(pins: list[Pin]) -> list[str]:
    with ThreadPoolExecutor(max_workers=8) as pool:
        return list(pool.map(latest, pins))


def short(pin: Pin, version: str) -> str:
    return version[:7] if pin.kind == "git" else version


def outdated() -> None:
    pins = collect_pins()
    width = max(len(pin.name) for pin in pins)
    behind = 0
    for pin, newest in zip(pins, latest_all(pins), strict=True):
        status = "ok" if newest == pin.current else "differs"
        behind += status != "ok"
        suffix = " (git: remote HEAD)" if pin.kind == "git" else ""
        print(f"{pin.name:<{width}}  {short(pin, pin.current):<9} {short(pin, newest):<9} {status}{suffix}")
    print(f"\n{behind} of {len(pins)} pins differ from the registry.")


def select(pins: list[Pin], names: list[str]) -> list[Pin]:
    if not names:
        return [pin for pin in pins if pin.kind == "npm"]
    known = {pin.name: pin for pin in pins}
    unknown = [name for name in names if name not in known]
    if unknown:
        raise ValueError(f"not a pinned package: {', '.join(unknown)}; run `outdated` for the names")
    return [known[name] for name in names]


def rewrite(old: str, new: str) -> list[Path]:
    touched = []
    for path in QUOTING_FILES:
        text = path.read_text()
        if old in text:
            path.write_text(text.replace(old, new))
            touched.append(path)
    return touched


def bump(names: list[str]) -> None:
    chosen = select(collect_pins(), names)
    bumped = []
    for pin, newest in zip(chosen, latest_all(chosen), strict=True):
        if newest == pin.current:
            continue
        touched = rewrite(f"{pin.prefix}@{pin.current}", f"{pin.prefix}@{newest}")
        if not touched:
            raise ValueError(f"{pin.prefix}@{pin.current} is not quoted in any pinned file")
        bumped.append(pin.name)
        print(f"{pin.name}: {short(pin, pin.current)} -> {short(pin, newest)} ({', '.join(p.name for p in touched)})")
    if not bumped:
        print("Nothing to bump.")
        return
    if "pi-herdr-agents" in bumped:
        print("pi-herdr-agents changed: re-derive agents/ from the new bundled roles and update the version quoted in README.md.")
    if not names:
        print("Git pins were left alone; name them explicitly to bump them.")
    print("Review `git diff`, run the tests, then `bash scripts/install.sh` and reload pi.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("outdated", help="compare every pin with its registry or remote HEAD")
    bump_parser = commands.add_parser("bump", help="rewrite pins to the latest release; npm pins only unless named")
    bump_parser.add_argument("names", nargs="*", help="pinned package names, as `outdated` prints them")
    args = parser.parse_args()
    if args.action == "outdated":
        outdated()
    else:
        bump(args.names)


if __name__ == "__main__":
    main()
