# weihung-agent-root

This repository is the source of truth for one user's pi setup. `scripts/install.sh` links its skills and rules into the home directory, and `scripts/pi-target.py` generates `~/.pi/agent/AGENTS.md` and manages pi settings, packages, and ported resources. It supports only pi; the last multi-harness version is the `legacy-claude-codex` tag.

## Language

Communicate with the user in Traditional Chinese, never Simplified Chinese. Write code, prompts, skills, rules, and agent instructions in English. Prompts, documents, and articles state the expected behavior directly, without defensive wording.

## Layout

- `pi/AGENTS.md.in`: the template for `~/.pi/agent/AGENTS.md`; `pi-target.py` appends the active model strategy's tiers.
- `pi/model-profiles.json`: the executable pi model and thinking tiers for each strategy.
- `pi/extensions/`: this repository's pi package, registered through `package.json`. Dispatch recovery, handoff, and pane balancing live in straw-boss.
- `skills/`: user skills linked into `~/.agents/skills/`. `managing-model-preferences` owns the strategy catalog.
- `agents/`: global `pi-herdr-agents` role overrides linked to `~/.pi/agent/agents/`. Each is the bundled role without its `tools:` allowlist; re-derive them when the `pi-herdr-agents` pin changes.
- `rules/`: user-global rules linked to `~/.pi/agent/rules/`. The template indexes every file by the work it covers, so a new rule also needs an entry there.
- `docs/specs/`: durable design records.

## Working here

- Source changes go through `aaaav-do` with an Alignment and Reality anchor before the first production edit.
- Keep the user-root layer thin: manage only behavior that is stable across projects and worth versioning. Machine credentials, login state, and project-specific workflows stay outside this repository.
- Installers never overwrite user files silently. A conflict fails unless `--force` is passed, which moves the old target to `~/.local/state/weihung-agent-root/backups/`, and uninstall restores what install replaced.
- Run the tests that cover a change before committing: `bash tests/install.sh`, `bash tests/uninstall.sh`, `python3 tests/<name>.py`, and `node --experimental-strip-types --test tests/<name>.mjs`. Exercise installer changes with `--home` pointing at a temporary directory before running them on the real home.
- After changing `pi/AGENTS.md.in`, `pi/model-profiles.json`, or the active strategy, run `bash scripts/install.sh` (or `python3 scripts/pi-target.py apply-profile --home "$HOME"` for a strategy switch) and reload pi.

## Commits

- Use Conventional Commits: `type(scope): subject`, with types such as `feat`, `fix`, `refactor`, `chore`, `docs`, and `test`, and a scope such as `pi`, `install`, `rules`, or `model-preferences`. The subject may be English or Traditional Chinese.
- Commit messages contain no AI tool attribution: no `Co-Authored-By`, `Claude-Session`, or similar trailers, and no mention of AI tools.
- Stage files by name; never `git add .` or `git add -A`.
