#!/usr/bin/env python3
"""List and bump the exact versions pinned in scripts/pi_root/pins.py, and keep them current on a schedule."""

import argparse
import importlib.util
import json
import os
import plistlib
import re
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from importlib.machinery import SourceFileLoader
from pathlib import Path
from typing import NamedTuple

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "scripts/pi_root/pins.py"
# Files that quote a pin verbatim and must move with it.
QUOTING_FILES = (TARGET, ROOT / "README.md", *sorted((ROOT / "tests").glob("*.py")),
                 *sorted((ROOT / "tests").glob("*.sh")), *sorted((ROOT / "tests").glob("*.mjs")))
NPM_PIN = re.compile(r"^(npm:(?:@[^/@]+/)?[^/@]+)@(.+)$")
GIT_PIN = re.compile(r"^(git:[^@]+)@([0-9a-f]{7,40})$")
PLAIN_NPM_PIN = re.compile(r"^([^/@:]+)@(.+)$")
MAIN_BRANCH = "main"
# npm pins `auto` leaves alone: bumping pi-herdr-agents also means re-deriving agents/ from its bundled roles.
MANUAL_PINS = {"pi-herdr-agents"}
STATE_DIR = Path.home() / ".local/state/weihung-agent-root"
STATE_FILE = STATE_DIR / "pi-autoupdate.json"
LOG_FILE = STATE_DIR / "pi-autoupdate.log"
LAUNCHD_LABEL = "com.weihung.agent-root.pi-autoupdate"
LAUNCHD_PLIST = Path.home() / "Library/LaunchAgents" / f"{LAUNCHD_LABEL}.plist"
SCHEDULE = {"Hour": 6, "Minute": 0}
SMOKE_TIMEOUT_SECONDS = 120
# Tools install.sh calls; launchd starts jobs with a bare PATH, so the schedule records where each lives.
# python3 comes first so its directory precedes /usr/bin, whose Python is too old for pi-target.py.
REQUIRED_TOOLS = ("python3", "pi", "npm", "node", "git", "bash")
OPTIONAL_TOOLS = ("herdr", "playwriter")
SYSTEM_PATH = ("/usr/bin", "/bin", "/usr/sbin", "/sbin")


class Pin(NamedTuple):
    kind: str  # "npm" or "git"
    prefix: str  # the text before "@<version>" exactly as the source files quote it
    current: str

    @property
    def name(self) -> str:
        return self.prefix.removeprefix("npm:").removeprefix("git:")


class FreshSourceLoader(SourceFileLoader):
    """Compile from source on every load: a cached .pyc is keyed on mtime in whole seconds and size, so a
    pin rewritten to an equally long version within the same second would still load as the old one."""

    def get_code(self, fullname: str):
        return self.source_to_code(self.get_data(self.path), self.path)


def load_target():
    spec = importlib.util.spec_from_file_location("pi_root_pins", TARGET, loader=FreshSourceLoader("pi_root_pins", str(TARGET)))
    if spec is None or spec.loader is None:
        raise ValueError(f"cannot load {TARGET}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def collect_pins() -> list[Pin]:
    target = load_target()
    pins = []
    for value in target.PACKAGES:
        source = value["source"] if isinstance(value, dict) else value
        if match := NPM_PIN.match(source):
            pins.append(Pin("npm", match[1], match[2]))
        elif match := GIT_PIN.match(source):
            pins.append(Pin("git", match[1], match[2]))
    for plain in (target.PLAYWRITER, target.THESIS_TOOLKIT):
        if match := PLAIN_NPM_PIN.match(plain):
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


class StepFailed(ValueError):
    """A verification or install step rejected an update."""


class RestoreFailed(RuntimeError):
    """Reinstalling the previous pins failed, so the machine no longer matches the repository."""


def git(*args: str) -> str:
    return run(["git", "-C", str(ROOT), *args])


def test_commands() -> list[list[str]]:
    tests = ROOT / "tests"
    return [
        *(["bash", str(path)] for path in sorted(tests.glob("*.sh"))),
        *([sys.executable, str(path)] for path in sorted(tests.glob("*.py"))),
        *(["node", "--experimental-strip-types", "--test", str(path)] for path in sorted(tests.glob("*.mjs"))),
    ]


def step(name: str, command: list[str], cwd: Path | None = None) -> None:
    result = subprocess.run(command, cwd=cwd or ROOT, capture_output=True, text=True)
    if result.returncode != 0:
        tail = "\n".join((result.stdout + result.stderr).strip().splitlines()[-15:])
        raise StepFailed(f"{name} failed: {' '.join(command[-2:])}\n{tail}")


def failing_tests() -> set[str]:
    failing = set()
    for command in test_commands():
        try:
            step("tests", command)
        except StepFailed:
            failing.add(command[-1])
    return failing


def smoke() -> None:
    """Start pi against the installed configuration; a package that fails to load makes pi exit non-zero."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    request = json.dumps({"id": "smoke", "type": "get_commands"}) + "\n"
    try:
        result = subprocess.run(["pi", "--mode", "rpc", "--no-session", "--offline", "--no-approve"], input=request,
                                cwd=STATE_DIR, capture_output=True, text=True, timeout=SMOKE_TIMEOUT_SECONDS)
    except subprocess.TimeoutExpired as error:
        raise StepFailed(f"smoke failed: pi did not answer within {SMOKE_TIMEOUT_SECONDS}s") from error
    if result.returncode != 0:
        raise StepFailed(f"smoke failed: pi exited {result.returncode}\n{result.stderr.strip()[-600:]}")
    replies = [json.loads(line) for line in result.stdout.splitlines() if line.startswith("{")]
    if not any(reply.get("type") == "response" and reply.get("success") and reply["data"]["commands"] for reply in replies):
        raise StepFailed("smoke failed: pi returned no command list")


def load_state() -> dict[str, dict[str, str]]:
    return json.loads(STATE_FILE.read_text()) if STATE_FILE.exists() else {"rejected": {}}


def save_state(state: dict[str, dict[str, str]]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")


def notify(message: str) -> None:
    print(message)
    if shutil.which("osascript") is None:
        return
    script = f"display notification {json.dumps(message, ensure_ascii=False)} with title \"pi autoupdate\""
    subprocess.run(["osascript", "-e", script], capture_output=True)


def attempt(names: list[str], known_failing: set[str]) -> None:
    """Bump the named pins, verify, install and commit; on failure restore the previous pins and reinstall them."""
    before = {pin.name: pin.current for pin in collect_pins()}
    bump(names)
    changed = git("diff", "--name-only").splitlines()
    if not changed:
        return
    installed = False
    try:
        for command in test_commands():
            if command[-1] not in known_failing:
                step("tests", command)
        installed = True
        step("install", ["bash", str(ROOT / "scripts/install.sh")])
        smoke()
    except StepFailed:
        git("checkout", "--", *changed)
        if installed:
            try:
                step("restore install", ["bash", str(ROOT / "scripts/install.sh")])
            except StepFailed as error:
                raise RestoreFailed(str(error)) from error
        raise
    after = {pin.name: pin.current for pin in collect_pins()}
    moved = [name for name in names if after[name] != before[name]]
    subject = f"chore(pi): bump {moved[0]} to {after[moved[0]]}" if len(moved) == 1 else "chore(pi): bump pinned packages"
    git("add", *changed)
    git("commit", "-m", subject, "-m", "\n".join(f"{name} {before[name]} -> {after[name]}" for name in moved))


def skip_reason() -> str | None:
    branch = git("branch", "--show-current")
    if branch != MAIN_BRANCH:
        return f"the checkout is on {branch or 'a detached HEAD'}, not {MAIN_BRANCH}"
    if git("status", "--porcelain"):
        return "the working tree has uncommitted changes"
    return None


def auto() -> None:
    print(f"== {datetime.now():%Y-%m-%d %H:%M:%S} pi-pins auto ==")
    if reason := skip_reason():
        notify(f"Skipped: {reason}.")
        return
    state = load_state()
    candidates = [pin for pin in collect_pins() if pin.kind == "npm" and pin.name not in MANUAL_PINS]
    newest = dict(zip((pin.name for pin in candidates), latest_all(candidates), strict=True))
    due = [pin.name for pin in candidates if newest[pin.name] != pin.current and state["rejected"].get(pin.name) != newest[pin.name]]
    if not due:
        print("Every pin is current or already rejected at its latest version.")
        return
    known_failing = failing_tests()
    if known_failing:
        print(f"Tests failing before any bump, skipped as a gate: {', '.join(sorted(known_failing))}")
    updated: list[str] = []
    failures: dict[str, str] = {}
    try:
        attempt(due, known_failing)
        updated = due
    except StepFailed as error:
        print(error)
        if len(due) == 1:
            failures[due[0]] = str(error)
        else:
            print("Retrying each pin on its own to isolate the failure.")
            for name in due:
                try:
                    attempt([name], known_failing)
                    updated.append(name)
                except StepFailed as single:
                    failures[name] = str(single)
    for name, error in failures.items():
        state["rejected"][name] = newest[name]
        print(f"Rejected {name}@{newest[name]}: {error}")
    save_state(state)
    parts = [f"Updated {len(updated)}: {', '.join(updated)}." if updated else None,
             "Rejected: " + ", ".join(f"{name}@{newest[name]} ({error.splitlines()[0]})" for name, error in failures.items()) + "." if failures else None,
             f"{len(known_failing)} test file(s) were already failing." if known_failing else None]
    notify(" ".join(part for part in parts if part))


def tool_directories() -> list[str]:
    directories: list[str] = []
    for tool in (*REQUIRED_TOOLS, *OPTIONAL_TOOLS):
        found = shutil.which(tool)
        if found is None:
            if tool in REQUIRED_TOOLS:
                raise ValueError(f"{tool} is not on PATH; the schedule needs it")
            continue
        directory = str(Path(found).parent)
        if directory not in directories:
            directories.append(directory)
    return [*directories, *(path for path in SYSTEM_PATH if path not in directories)]


def launchd_plist() -> dict:
    return {
        "Label": LAUNCHD_LABEL,
        "ProgramArguments": [sys.executable, str(Path(__file__).resolve()), "auto"],
        "StartCalendarInterval": SCHEDULE,
        "StandardOutPath": str(LOG_FILE),
        "StandardErrorPath": str(LOG_FILE),
        "EnvironmentVariables": {"PATH": ":".join(tool_directories()), "HOME": str(Path.home())},
    }


def launchctl(*args: str, check: bool = True) -> None:
    result = subprocess.run(["launchctl", *args], capture_output=True, text=True)
    if check and result.returncode != 0:
        raise ValueError(f"launchctl {' '.join(args)} failed: {result.stderr.strip()}")


def schedule() -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    LAUNCHD_PLIST.parent.mkdir(parents=True, exist_ok=True)
    LAUNCHD_PLIST.write_bytes(plistlib.dumps(launchd_plist()))
    domain = f"gui/{os.getuid()}"
    launchctl("bootout", f"{domain}/{LAUNCHD_LABEL}", check=False)
    launchctl("bootstrap", domain, str(LAUNCHD_PLIST))
    print(f"Scheduled daily at {SCHEDULE['Hour']:02d}:{SCHEDULE['Minute']:02d}: {LAUNCHD_PLIST}\nLog: {LOG_FILE}")


def unschedule() -> None:
    launchctl("bootout", f"gui/{os.getuid()}/{LAUNCHD_LABEL}", check=False)
    LAUNCHD_PLIST.unlink(missing_ok=True)
    print(f"Removed {LAUNCHD_LABEL}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    commands.add_parser("outdated", help="compare every pin with its registry or remote HEAD")
    bump_parser = commands.add_parser("bump", help="rewrite pins to the latest release; npm pins only unless named")
    bump_parser.add_argument("names", nargs="*", help="pinned package names, as `outdated` prints them")
    commands.add_parser("auto", help="bump every npm pin to its latest release, keep it only if tests, install and a pi load pass")
    commands.add_parser("schedule", help="run `auto` daily through launchd")
    commands.add_parser("unschedule", help="remove the launchd schedule")
    args = parser.parse_args()
    if args.action == "outdated":
        outdated()
    elif args.action == "auto":
        try:
            auto()
        except Exception as error:
            notify(f"Crashed: {str(error).splitlines()[0]} See {LOG_FILE}.")
            raise
    elif args.action == "schedule":
        schedule()
    elif args.action == "unschedule":
        unschedule()
    else:
        bump(args.names)


if __name__ == "__main__":
    main()
