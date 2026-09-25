---
name: orchestrator-handoff
description: Transfer one main-agent scope and its unfinished Pi dispatches to a new Herdr pane.
---

# Orchestrator handoff

Use `pi-intercom` to find related main sessions and exchange concise facts. For an ownership transfer, call `dispatch_control` with `action: "handoff"` and a `summary` containing the scope, decisions, anchor, pending user input, and unfinished dispatches. The extension supplies the current Pi session ID and working directory.

The command creates a visible Herdr tab, passes the summary, and commits ownership after the receiver is ready. Read the returned pane ID and handoff ID. The receiving session imports committed dispatches on startup, including after its first process stops before import. Give the user the new pane ID and stop work in the originating main session after confirming the new session started.

Result delivery is once while the owner process runs. Across a process crash between sending a result and recording its receipt, delivery is at least once, so the receiving session may see the result again.
