import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent


class DispatchCliTest(unittest.TestCase):
    def test_roll_call_reattach_and_handoff(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            agent = home / ".pi/agent"
            ledger = agent / "dispatch-ledger/owner.json"
            ledger.parent.mkdir(parents=True)
            child = home / "child.jsonl"
            child.write_text("")
            ledger.write_text(json.dumps([{
                "id": "child-1", "name": "worker", "task": "Task", "cwd": str(home),
                "sessionFile": str(child), "paneId": "w1:p2", "status": "running",
            }]))
            bin_dir = home / "bin"
            bin_dir.mkdir()
            fake = bin_dir / "herdr"
            fake.write_text("""#!/usr/bin/env python3
import json, os, sys
from pathlib import Path
args = sys.argv[1:]
with Path(os.environ['HERDR_TEST_LOG']).open('a') as out:
    out.write(json.dumps(args) + '\\n')
if args[:2] == ['pane', 'process-info']:
    processes = [{'name': 'zsh'}] if args[-1] == 'w1:p3' else []
    print(json.dumps({'result': {'process_info': {'foreground_processes': processes}}}))
elif args[:2] == ['tab', 'create']:
    Path(os.environ['HERDR_TEST_LOG']).with_suffix('.handoff').write_text(next(
        value.split('=', 1)[1] for index, value in enumerate(args) if index > 0 and args[index - 1] == '--env' and value.startswith('PI_HANDOFF_ID=')
    ))
    print(json.dumps({'result': {'root_pane': {'pane_id': 'w1:p3'}}}))
elif args[:2] == ['agent', 'start']:
    transfer_id = Path(os.environ['HERDR_TEST_LOG']).with_suffix('.handoff').read_text()
    ready = Path(os.environ['PI_CODING_AGENT_DIR']) / 'handoffs' / f'{transfer_id}.ready'
    ready.write_text('receiver')
    print(json.dumps({'result': {}}))
elif args[:2] == ['pane', 'run']:
    pass
else:
    print(json.dumps({'result': {}}))
""")
            fake.chmod(0o755)
            log = home / "herdr.log"
            env = {**os.environ, "HOME": str(home), "PI_CODING_AGENT_DIR": str(agent),
                   "PI_SESSION_ID": "owner", "HERDR_ENV": "1", "HERDR_WORKSPACE_ID": "w9", "HERDR_TEST_LOG": str(log),
                   "PATH": str(bin_dir) + os.pathsep + os.environ["PATH"]}

            def call(*args):
                return subprocess.run(["python3", str(ROOT / "scripts/pi-dispatch.py"), *args],
                                      env=env, check=True, capture_output=True, text=True).stdout

            self.assertIn("child-1 | running", call("roll-call"))
            self.assertIn("Resumed worker in w1:p2", call("reattach", "child-1"))
            self.assertIn("active dispatches: 1", call("handoff", "--cwd", str(home), "--summary", "Continue the task"))
            calls = [json.loads(line) for line in log.read_text().splitlines()]
            self.assertTrue(any(args[:2] == ["pane", "run"] and "PI_SUBAGENT_SESSION" in args[-1] for args in calls))
            self.assertTrue(any(args[:2] == ["tab", "create"] and "PI_HANDOFF_ID=" in " ".join(args) for args in calls))
            self.assertTrue(any(args[:2] == ["tab", "create"] and args[args.index("--workspace") + 1] == "w9" for args in calls))
            self.assertTrue(any(args[:2] == ["agent", "start"] and "--kind" in args for args in calls))
            self.assertTrue(any(args[:2] == ["agent", "prompt"] and "Continue the task" in args[-1] for args in calls))
            self.assertEqual(json.loads(ledger.read_text())[0]["status"], "transferred")
            transfers = list((agent / "handoffs").glob("*.json"))
            self.assertEqual(len(transfers), 1)
            self.assertEqual(json.loads(transfers[0].read_text())["dispatches"][0]["status"], "running")


if __name__ == "__main__":
    unittest.main()
