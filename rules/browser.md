# Browser

- Default to a separate headless `agent-browser` session. Attach to the user's own Chrome only when the task needs its login state.
- The user's Chrome exposes user-approved remote debugging on port 9222 without an HTTP discovery endpoint, so `--auto-connect` fails. Attach with `agent-browser --cdp ws://127.0.0.1:9222/devtools/browser --pin-tab`; if that fails, ask the user to allow remote debugging in Chrome instead of relaunching it.
- In the user's Chrome, open a tab with `tab new` and act only there. Never navigate, type into, or close tabs the user opened, and finish with `tab close` rather than `close`.
- Before a submit that saves, deletes, pays, grants access, or publishes, stop and show the user what will change. Hand logins, CAPTCHAs, and two-factor prompts to the user.
