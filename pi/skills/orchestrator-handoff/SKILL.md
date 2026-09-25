---
name: orchestrator-handoff
description: Transfer one main-agent scope and its unfinished Pi dispatches to a new Herdr pane.
---

# Orchestrator handoff

Use `pi-intercom` to find related main sessions and exchange concise facts. For an ownership transfer, call `dispatch_control` with `action: "handoff"` and a `summary` containing the scope, decisions, anchor, pending user input, and unfinished dispatches. The extension supplies the current Pi session ID and working directory.

The command creates a visible Herdr tab, passes the summary, and transfers the unfinished dispatch ledger. Read the returned pane ID and handoff ID. The receiving Pi process imports the ledger at startup and reports later child completions. Give the user the new pane ID and stop work in the originating main session after confirming the new session started.
