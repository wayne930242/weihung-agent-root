---
name: publishing-pi-extensions
description: Use when creating a new pi extension package, or releasing a new version of one, for npm and the pi package gallery.
---

# Publishing Pi Extensions

A pi extension ships as its own public repository under `~/projects/<name>`, published to npm as `<name>`, and listed in the pi package gallery at `https://pi.dev/packages/<name>`.
`~/projects/pi-robot-hand` is the minimal template: copy its `package.json`, `tsconfig.json`, `.gitignore`, `LICENSE`, `.github/workflows/publish.yml`, and `tests/imports.test.ts`, then adapt names and descriptions.
`~/projects/pi-secret-drop` shows a package that also ships a skill and compiled helper scripts.

## New package

### 1. Claim the name

`npm view <name>` and `gh repo view wayne930242/<name>` both report not found.
Name choices belong to the user; offer candidates that pass this check.

**Complete when:** the user picked a name that is free on npm and GitHub.

### 2. Build

- `package.json` carries the `pi-package` keyword (this is what lists it in the gallery), `pi.extensions` pointing at `./src/index.ts`, `files` limited to what pi loads, pi packages as `peerDependencies` with `"*"`, and the same packages pinned to their latest versions in `devDependencies`.
- Relative imports inside `src/` end in `.ts`: pi reloads TypeScript on `/reload`, while Node caches `.js` modules for the life of the process.
- Tests drive the registered tool's `execute()` against a minimal `ExtensionAPI` and `ExtensionContext`, as in `pi-robot-hand/tests/tool.test.ts`.

**Complete when:** `npm run check` and `npm test` pass, and `npm pack --dry-run` lists only the intended files.

### 3. Exercise it in a real pi

Run pi in tmux with only this extension loaded, then drive it with `tmux send-keys` and read it with `tmux capture-pane -p`:

```bash
tmux new-session -d -s ext -x 160 -y 50 "pi --no-session -ne -e $HOME/projects/<name>/src/index.ts --model openai-codex/gpt-6-luna; sleep 60"
```

`-ne` also drops the claude-bridge extension, so pick an `openai-codex/*` model.
The trailing `sleep` keeps the pane open long enough to read a startup error.
Save and restore the user's clipboard (`pbpaste`/`pbcopy`) around clipboard checks.

**Complete when:** every user-visible branch of the extension ran in the TUI and its captured screen matches the contract.

### 4. Push to GitHub

Commit with Conventional Commits, staging files by name, then:

```bash
gh repo create wayne930242/<name> --public --description "<one line>" --source . --remote origin --push
```

**Complete when:** `origin/main` holds the commit.

### 5. First publish by the user

The npm account `weihung1017` authenticates with a security key, which needs the user's browser, so the user runs the first publish.
Hand it over with `robot_hand`:

```bash
cd ~/projects/<name> && npm publish --access public --auth-type=web
```

Run `npm whoami` first; on a 401, hand over `npm login` before the publish.

**Complete when:** `npm view <name> version` prints the released version.

### 6. Trusted publishing

The local npm may lack `npm trust`, so run it through the latest npm:

```bash
npx -y npm@latest trust github <name> --repo wayne930242/<name> --file publish.yml --allow-publish --allow-stage-publish --yes
```

**Complete when:** `npx -y npm@latest trust list <name>` shows the GitHub `publish.yml` entry with `publish, stage publish`.

### 7. Install

- During development, `pi install ~/projects/<name>` loads the working tree; `/reload` picks up edits.
- After release, `pi remove ~/projects/<name>` then `pi install npm:<name>@<version>`, and the user runs `/reload`.
- To install it on every machine, add the pinned spec to `PACKAGES` in `scripts/pi-target.py`; this is the user's call.

**Complete when:** `~/.pi/agent/settings.json` lists `npm:<name>@<version>` and `curl -sL -o /dev/null -w '%{http_code}' https://pi.dev/packages/<name>` returns `200`.

## New release

1. Bump `version` in `package.json`, commit, and push `main` with a matching tag: `git tag v<version> && git push origin main v<version>`.
2. The `Publish` workflow runs check and tests, confirms the tag matches the version, and publishes through trusted publishing.
3. Move the install to the new pin with `pi install npm:<name>@<version>`, and bump `PACKAGES` in `scripts/pi-target.py` when it is listed there.

**Complete when:** `gh run list --repo wayne930242/<name> --limit 1` shows the run succeeded and `npm view <name> version` prints the new version.
