---
description: "Agents stop only the processes they started"
condition: '\b(pkill|killall)\b'
scope: "tool:bash"
repeatMode: after-gap
repeatGap: 1
---

Do not use `pkill` or `killall`: a name or `-f` pattern also matches processes that other workers and the user started, such as their headless Chromes and dev servers.

Stop only what you started: `kill <pid>` with the PID you recorded, `MonitorStop` for a monitor, or `agent-browser --session <name> close` for your browser session.
