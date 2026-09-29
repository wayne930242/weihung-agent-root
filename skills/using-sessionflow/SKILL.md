---
name: using-sessionflow
description: Use when the user mentions SessionFlow or "sf", or asks to plan, schedule, move, or review focus sessions on their calendar.
---

# Using SessionFlow

SessionFlow ("sf") is the user's macOS app that fits focus sessions into gaps in Calendar and tracks them while they run. It starts from Login Items and serves a local MCP server that pi reaches as `sessionflow` (`http://127.0.0.1:8787/mcp`, bearer token from `SESSIONFLOW_MCP_TOKEN` in `~/.zshenv`). Its `learn` tool returns the full tool guide.

## The user's day

- Weekdays run 09:00–18:00. Lunch is a recurring 13:00–14:00 "午休" event on the Work calendar; SessionFlow schedules around calendar events, so that event is what blocks lunch.
- Preset `平日` is the standard day: Planning 10 min, 4 Work × 45 min, 1 Deep × 90 min right after the first Work, 2 Side × 30 min.
- Session types: Planning `#plan` opens the day; Work `#work` is ordinary focused work; Deep `#deep` is the one long uninterrupted block for the hardest thinking; Side `#side` is admin and messages.

## Scheduling

SessionFlow computes the times, but nothing reaches the calendar until a commit, and nothing runs daily on its own.

1. Set inputs with `apply_preset`, `set_config`, and `set_tasks`. When the user names tasks, pass them through `set_tasks` so they become session titles.
2. Run `regenerate_schedule` for the date and show the preview to the user as a time table.
3. After the user confirms, run `commit_schedule`, then `get_day` for that date.

**Complete when:** every committed session appears in `get_day` at the times the user confirmed.

- Preview session ids change on every regeneration: `set_freeze {"frozen": true}` before `move_session` on a preview session, and unfreeze after the commit.
- For today, regeneration starts from the current time.
- A one-off schedule, such as a single test session, rewrites the active config. Re-apply `平日` afterwards and check it with `get_config`.

## Outside the MCP

- Session Awareness settings (sounds, Commit Mode) have no MCP tool. They are one JSON value in UserDefaults domain `com.kibermaks.SessionFlow`, key `SessionFlow.SessionAwarenessConfig`; absent fields fall back to app defaults. Quit the app, write the value, relaunch. The user keeps only the start (Hero) and end (Gong) sounds; ambient, ending-soon, and presence-reminder sounds are off.
- Focus ratings, alignment, and Commit Mode goals are stored in the calendar event notes: `#flow🚀` `#flow✅` `#flow🌗` `#flow📱` `#flow❌` for Focus, `#flowalign0`–`#flowalign4` for Off, Maint, Support, Strat, Direct, and a `#flowgoal:` section for goals. This is an internal format; the user rates through the timeline badge on the session, because the end-of-session prompt closes after 30 seconds.
- The main window lives on AeroSpace workspace P (`alt-p`); the Mini-Player floats outside AeroSpace.
