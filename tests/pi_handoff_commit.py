import importlib.util
import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


ROOT = Path(__file__).resolve().parent.parent
SPEC = importlib.util.spec_from_file_location("pi_dispatch", ROOT / "scripts/pi-dispatch.py")
DISPATCH = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DISPATCH)


class HandoffCommitTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.home = Path(self.temporary.name)
        self.agent = self.home / "agent"
        self.ledger = self.agent / "dispatch-ledger"
        self.handoffs = self.agent / "handoffs"
        self.ledger.mkdir(parents=True)
        self.owner_file = self.ledger / "owner.json"
        self.owner_file.write_text(json.dumps([{
            "id": "worker", "name": "worker", "task": "Finish", "cwd": str(self.home),
            "sessionFile": str(self.home / "child.jsonl"), "status": "running",
        }]))
        for name, value in (("AGENT_DIR", self.agent), ("LEDGER_DIR", self.ledger), ("HANDOFF_DIR", self.handoffs)):
            patcher = patch.object(DISPATCH, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        patcher = patch.object(DISPATCH.uuid, "uuid4", return_value=SimpleNamespace(hex="transfer"))
        patcher.start()
        self.addCleanup(patcher.stop)

    def run_handoff(self, fail=None):
        original_write = DISPATCH.write_json

        def write(path, data):
            if fail == "prepare" and path == self.handoffs / "transfer.json":
                raise OSError("prepare failed")
            if fail == "commit" and path == self.handoffs / "transfer.json" and data.get("state") == "committed":
                raise OSError("commit failed")
            if fail == "ledger" and path == self.owner_file:
                raise OSError("ledger view failed")
            return original_write(path, data)

        def start(_name, _pane):
            (self.handoffs / "transfer.ready").write_text("receiver")

        with patch.object(DISPATCH, "write_json", side_effect=write), \
             patch.object(DISPATCH, "new_pane", return_value="test:pane"), \
             patch.object(DISPATCH, "start_receiving_agent", side_effect=start), \
             patch.object(DISPATCH, "herdr", return_value={}), redirect_stdout(io.StringIO()) as output:
            if fail in ("prepare", "commit"):
                with self.assertRaises(OSError):
                    DISPATCH.handoff("owner", str(self.home), "Continue")
            else:
                DISPATCH.handoff("owner", str(self.home), "Continue")
            return output.getvalue()

    def test_prepare_failure_retains_owner(self):
        self.run_handoff("prepare")
        self.assertEqual(json.loads(self.owner_file.read_text())[0]["status"], "running")
        self.assertFalse((self.handoffs / "transfer.json").exists())

    def test_commit_failure_retains_owner(self):
        self.run_handoff("commit")
        self.assertEqual(json.loads(self.owner_file.read_text())[0]["status"], "running")
        self.assertFalse((self.handoffs / "transfer.json").exists())

    def test_ledger_view_failure_keeps_committed_owner(self):
        output = self.run_handoff("ledger")
        self.assertIn("active dispatches: 1", output)
        self.assertEqual(json.loads((self.handoffs / "transfer.json").read_text())["state"], "committed")
        self.assertEqual(json.loads(self.owner_file.read_text())[0]["status"], "running")
        with redirect_stdout(io.StringIO()) as inventory:
            DISPATCH.roll_call("owner")
        self.assertIn("worker | transferred", inventory.getvalue())
        with self.assertRaises(ValueError):
            DISPATCH.reattach("owner", "worker")


if __name__ == "__main__":
    unittest.main()
