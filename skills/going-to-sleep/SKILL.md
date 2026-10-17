---
name: going-to-sleep
description: Use when the user is going to rest or sleep and leaves a last round of work (睡前最後一輪, 我要睡了, 準備休息, 做完就讓電腦睡), or says they are up again (我起床了, 我醒了, 早安).
---

# Going to sleep

The user is gone until morning: finish the last round on your own, then put the Mac to sleep if they asked for it. Never run `pmset` without that request.

1. **Record the mandate** in the daily memory log: the work to finish, what may be merged, pushed, or deployed, and whether the Mac should sleep. Later wakes act on that entry.
2. **Tell the other sessions** the user is resting, once each, skipping yourself; a `subagent-chat-*` name can be a main session, so do not filter by name:
   `cli=~/.pi/agent/npm/node_modules/pi-intercom/cli.mjs; node $cli list --json | jq -r --arg me "$PI_SESSION_ID" '.sessions[] | select(.id != $me) | .id' | while read -r id; do node $cli send --to "$id" --text "<message>"; done`
   Ask them to reach a safe stopping point and keep user decisions for the morning.
3. **Set a safety deadline** with a one-shot `LoopCreate` (about two hours) that pushes what is verified and sleeps the Mac, so a stuck worker cannot keep it awake all night.
4. **Finish the round without the user**: no `ask_user`, `robot_hand`, or `secret_drop`. A failing test is yours to fix, not a reason to wait; work that still cannot be verified stays on its local branch and goes into the daily log. Push only what the mandate covers.
5. **Sleep**: broadcast that the Mac is going to sleep, wait up to five minutes for a session that must stop something first, delete the deadline loop, stop any `caffeinate` you started, then run `pmset sleepnow`.

**Complete when:** the mandate is done or logged as left over, and the Mac is asleep or the user did not ask for sleep.

## Waking up

1. **Wake the other sessions** with the same broadcast: the user is back, so resume interrupted workers with `subagent_resume`, recheck monitors and services the sleep paused, and bring held decisions to the user.
2. **Present the morning list** from the daily log: what landed, what is left over, and what needs the user.
3. **Hand over cleanup** the tools refused (worktrees, panes, processes) as one command through `robot_hand`, after confirming each target is pushed or no longer needed.
