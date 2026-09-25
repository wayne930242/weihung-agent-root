---
name: dispatch-recovery
description: List and resume Pi Herdr dispatches after a main or worker session restart.
---

# Dispatch recovery

`pi-herdr-agents` performs normal dispatch and delivers results automatically. The local extension records each started `subagent` result under the Pi agent directory. On a parent process restart, it watches unfinished child sessions and delivers their completion.

Use the `dispatch_control` tool with `action: "roll-call"` to list records for the current Pi session. Use `action: "reattach"` and the dispatch `id` when a worker pane has returned to its shell and its session needs to continue. The tool resumes that child session in its pane and the extension continues watching the completion sidecar.

Check the worker pane before reattaching. If the pane still has a foreground process, keep that process; the command reports the condition without sending another task. After a handoff, the receiving main session uses its own roll-call; the handoff imports running records when that Pi process starts.
