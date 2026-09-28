# Browser

- Run full end-to-end work in the user's Chrome through the Playwriter CLI. Use a headless `agent-browser` session only for UI checks that need no session and for checks that bypass authentication.
- Call the installed `playwriter` binary, never `npx playwriter@latest`: a version mismatch makes the CLI restart the relay. Read `playwriter skill` for the API before first use in a session.
- Pi starts the relay on `127.0.0.1:19988` at session start. When a command reports the extension is not connected, ask the user to open Chrome or reload the Playwriter extension; never relaunch Chrome or use `--remote-debugging-port`.
- Start each task with `playwriter session new --tab-group <task> --tab-group-color <color>` and pass `-s <id>` to every command. Open pages with `context.newPage()`, keep them in `state`, and act only on them. Creating or closing a tab takes the extension several seconds, so open a page in its own call before navigating, or pass `--timeout 30000`.
- `context.pages()` also lists tabs the user handed over by clicking the extension icon. Act on such a tab only when the user asks for it, and never navigate, type into, or close the user's other tabs.
- Finish by closing the pages you opened and running `playwriter session delete <id>`. A relay restart resets session ids and leaves earlier pages open, so close those by URL.
- Before a submit that saves, deletes, pays, grants access, or publishes, stop and show the user what will change. Hand logins, CAPTCHAs, and two-factor prompts to the user.
