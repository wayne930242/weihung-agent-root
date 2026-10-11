---
name: working-remotely
description: Use when the user says they are leaving and will control pi remotely (開始遠端, 我要出門, 遠端控制你), or says they are back (結束遠端, 我回家了, 回來了).
---

# Working remotely

While the user is away, they read and answer pi from a remote client. Tools that open a dialog or need their hands on this Mac do not reach them there, so remote mode changes how every coordinator talks to them until they announce they are back.

## Starting remote mode

1. Keep the Mac awake: start `exec caffeinate -ims` with `MonitorCreate` (timeout 0), then confirm its PID with `pgrep -fl "caffeinate -ims"`. Skip this when another session already runs one. Tell the user the lid must stay open.
2. Write the flag file `~/.local/state/weihung-agent-root/remote-mode` containing the start time, so a session started later can tell remote mode is on.
3. Broadcast the rules below with `intercom` to every other coordinator session (`intercom list`; coordinators are the long-lived main sessions, not dispatched workers), and ask each to pass them to the coordinators it dispatched.
4. Record the start in the daily memory log.

## Rules while remote

- Ask questions as plain chat text, never through `ask_user`. Give numbered options with a recommendation and its reason, so the user can answer with a number.
- Do not use `robot_hand`, `secret_drop`, or anything else that needs the user at this Mac. Write down what needs their hands and present it when they are back.
- Postpone cleanup until they are back: removing worktrees, deleting branches, closing panes, and stopping processes or monitors started for the work. Leave them as they are and keep a list.
- Everything else follows the usual rules, including the confirmation gates for production, external, and destructive actions; ask for those in chat text.

## Ending remote mode

1. Broadcast the end with `intercom` to the same coordinators.
2. Delete the flag file.
3. Present in one message: the deferred cleanup list, the commands or credential steps that need the user's hands, and any answer still pending. Then resume normal behavior, using `ask_user` and `robot_hand` again.
4. Ask whether to stop `caffeinate`; stop it with `MonitorStop` once they agree and confirm the PID is gone.
5. Record the end in the daily memory log.

**Complete when:** the flag file is gone, every coordinator received the end broadcast, and the user has the deferred list.
