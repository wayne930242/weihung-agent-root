#!/usr/bin/env python3
"""Inspect and recover Pi dispatches recorded by the local extension."""

import argparse
from contextlib import contextmanager
import json
import os
import shlex
import subprocess
import time
import uuid
from pathlib import Path


AGENT_DIR = Path(os.environ.get("PI_CODING_AGENT_DIR", str(Path.home() / ".pi/agent")))
LEDGER_DIR = AGENT_DIR / "dispatch-ledger"
HANDOFF_DIR = AGENT_DIR / "handoffs"
SUBAGENT_EXTENSION = AGENT_DIR / "npm/node_modules/pi-herdr-agents/pi-extension/subagents/subagent-done.ts"


def session_id(value):
    result = value or os.environ.get("PI_SESSION_ID")
    if not result:
        raise ValueError("Pass --session-id from the Pi dispatch_control tool")
    return result


def ledger_path(owner):
    return LEDGER_DIR / f"{owner}.json"


def read_ledger(owner):
    path = ledger_path(owner)
    return json.loads(path.read_text()) if path.exists() else []


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        temporary.write_text(json.dumps(data, indent=2) + "\n")
        temporary.chmod(0o600)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


@contextmanager
def lock_ledger(owner):
    LEDGER_DIR.mkdir(parents=True, exist_ok=True)
    lock = LEDGER_DIR / f".{owner}.lock"
    deadline = time.monotonic() + 5
    while True:
        try:
            lock.mkdir()
            break
        except FileExistsError:
            if time.monotonic() >= deadline:
                raise RuntimeError(f"Timed out waiting for dispatch ledger {owner}")
            time.sleep(0.01)
    try:
        yield
    finally:
        lock.rmdir()


def herdr(*args):
    if os.environ.get("HERDR_ENV") != "1":
        raise ValueError("Herdr is unavailable; open Pi in a Herdr pane first")
    try:
        result = subprocess.run(["herdr", *args], check=True, text=True, capture_output=True)
    except subprocess.CalledProcessError as error:
        detail = (error.stderr or error.stdout or "").strip()
        raise RuntimeError(f"herdr {' '.join(args[:2])} failed: {detail}") from error
    return json.loads(result.stdout) if result.stdout.strip() else {}


def new_pane(cwd, label, env=None):
    args = ["tab", "create", "--cwd", cwd, "--label", label, "--no-focus"]
    workspace = os.environ.get("HERDR_WORKSPACE_ID")
    if workspace:
        args.extend(["--workspace", workspace])
    if env:
        for key, value in env.items():
            args.extend(["--env", f"{key}={value}"])
    response = herdr(*args)
    pane = response["result"]["root_pane"]["pane_id"]
    for _ in range(25):
        try:
            processes = herdr("pane", "process-info", "--pane", pane)["result"]["process_info"]["foreground_processes"]
        except RuntimeError:
            processes = []
        if any(item.get("name") in ("zsh", "bash", "fish", "sh") for item in processes):
            return pane
        time.sleep(0.2)
    raise RuntimeError(f"New pane {pane} did not reach an interactive shell")


def pane_available(pane):
    try:
        response = herdr("pane", "process-info", "--pane", pane)
    except RuntimeError:
        return None
    processes = response["result"]["process_info"]["foreground_processes"]
    return not processes or all(item.get("name") in ("zsh", "bash", "fish", "sh") for item in processes)


def start_receiving_agent(name, pane):
    for attempt in range(25):
        try:
            herdr("agent", "start", name, "--kind", "pi", "--pane", pane, "--", "--name", name)
            return
        except RuntimeError as error:
            if "agent_pane_busy" not in str(error) or attempt == 24:
                raise
            time.sleep(0.2)


def roll_call(owner):
    records = read_ledger(owner)
    for item in records:
        pane = item.get("paneId") or "unknown"
        print(f"{item['id']} | {item['status']} | {item['name']} | {pane} | {item['sessionFile']}")
    if not records:
        print("No recorded dispatches")


def reattach(owner, dispatch_id):
    records = read_ledger(owner)
    item = next((record for record in records if record["id"] == dispatch_id), None)
    if not item:
        raise ValueError(f"Unknown dispatch: {dispatch_id}")
    if item["status"] != "running":
        raise ValueError(f"Dispatch is {item['status']}; inspect its recorded session")
    pane = item.get("paneId")
    available = pane_available(pane) if pane else None
    if pane and available is False:
        raise ValueError(f"Pane {pane} still has a foreground process; inspect it before resuming")
    if available is None:
        pane = new_pane(item["cwd"], f"resume-{item['name']}")
        item["paneId"] = pane
        write_json(ledger_path(owner), records)
    env = {
        "PI_SUBAGENT_SESSION": item["sessionFile"],
        "PI_SUBAGENT_ID": item["id"],
        "PI_SUBAGENT_NAME": item["name"],
        "PI_SUBAGENT_AUTO_EXIT": "1",
        "PI_SUBAGENT_SURFACE": pane,
    }
    args = ["pi", "--session", item["sessionFile"]]
    if SUBAGENT_EXTENSION.exists():
        args += ["-e", str(SUBAGENT_EXTENSION)]
    args += ["Continue the assigned task from this session. Report the result when complete."]
    command = "cd " + shlex.quote(item["cwd"]) + " && " + " ".join(f"{key}={shlex.quote(value)}" for key, value in env.items()) + " " + shlex.join(args)
    herdr("pane", "run", pane, command)
    print(f"Resumed {item['name']} in {pane}; completion will be delivered to the owner session")


def handoff(owner, cwd, summary):
    transfer_id = uuid.uuid4().hex
    handoff_file = HANDOFF_DIR / f"{transfer_id}.json"
    with lock_ledger(owner):
        current = read_ledger(owner)
        records = [record.copy() for record in current if record["status"] == "running"]
        write_json(handoff_file, {"from": owner, "summary": summary, "dispatches": records})
        for record in current:
            if record["status"] == "running":
                record["status"] = "transferred"
        write_json(ledger_path(owner), current)

    def restore_owner():
        transferred_ids = {record["id"] for record in records}
        with lock_ledger(owner):
            current = read_ledger(owner)
            for record in current:
                if record["id"] in transferred_ids and record["status"] == "transferred":
                    record["status"] = "running"
            write_json(ledger_path(owner), current)
        handoff_file.unlink(missing_ok=True)

    try:
        pane = new_pane(cwd, f"handoff-{transfer_id[:8]}", {"PI_HANDOFF_ID": transfer_id})
    except Exception:
        restore_owner()
        raise
    prompt = f"You are taking over a main-agent scope. Handoff ID: {transfer_id}. Summary: {summary} Use the dispatch_control tool with action roll-call to inspect active dispatches, then continue the work."
    name = f"handoff-{transfer_id[:8]}"
    try:
        start_receiving_agent(name, pane)
    except RuntimeError as error:
        if "agent_pane_busy" not in str(error):
            raise RuntimeError(f"Handoff {transfer_id} may have started in pane {pane}; inspect it before retrying") from error
        try:
            herdr("pane", "close", pane)
        except RuntimeError:
            raise RuntimeError(f"Handoff {transfer_id} may have started in pane {pane}; inspect it before retrying") from error
        restore_owner()
        raise
    herdr("agent", "prompt", name, prompt)
    print(f"Handoff {transfer_id} started in pane {pane}; active dispatches: {len(records)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("roll-call", "reattach", "handoff"))
    parser.add_argument("id", nargs="?")
    parser.add_argument("--session-id")
    parser.add_argument("--cwd", default=os.getcwd())
    parser.add_argument("--summary")
    args = parser.parse_args()
    owner = session_id(args.session_id)
    if args.action == "roll-call":
        roll_call(owner)
    elif args.action == "reattach":
        if not args.id:
            parser.error("reattach requires a dispatch ID")
        reattach(owner, args.id)
    else:
        if not args.summary:
            parser.error("handoff requires --summary")
        handoff(owner, args.cwd, args.summary)


if __name__ == "__main__":
    main()
