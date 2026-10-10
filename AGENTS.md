# weihung-agent-root

This repository is the source of truth for one user's pi setup. `scripts/install.sh` links its skills and rules into the home directory, and `scripts/pi-target.py` generates `~/.pi/agent/AGENTS.md` and manages pi settings, packages, and ported resources. It supports only pi; the last multi-harness version is the `legacy-claude-codex` tag.

## Language

Communicate with the user in Traditional Chinese, never Simplified Chinese. Write code, prompts, skills, rules, and agent instructions in English. Prompts, documents, and articles state the expected behavior directly, without defensive wording.

## Layout

- `scripts/pi_root/`: the logic behind `scripts/pi-target.py`, one module per managed part; pinned package versions live in `pins.py`.
- `pi/AGENTS.md.in`: the template for `~/.pi/agent/AGENTS.md`. It names `pi-herdr-agents` roles but no model.
- `pi/herdr-agents-models.json`: the `pi-herdr-agents` `models` object (`default`, `agents` per role, `tasks` per category). The installer writes it into `~/.pi/agent/herdr-agents/config.json`. pi's default model stays in `~/.pi/agent/settings.json`, outside this repository. There is no model strategy profile or tier role; do not reintroduce one (`tests/pi_configs.py` guards this).
- `pi/extensions/`: this repository's pi package, registered through `package.json`. Dispatch recovery, handoff, and pane balancing live in straw-boss.
- `skills/`: user skills linked into `~/.agents/skills/`. `skills/orchestrate` is our trimmed copy of the `pi-herdr-roles` orchestrate skill; the installed pack filters its own copy out.
- `agents/`: global `pi-herdr-agents` role overrides linked to `~/.pi/agent/agents/`. Each derives from the `pi-herdr-roles` role of the same name without its `tools:` allowlist; `planner` comes from the pack unchanged. Re-derive them when the `pi-herdr-roles` pin changes.
- `rules/`: user-global rules linked to `~/.pi/agent/rules/`. The template indexes every file by the work it covers, so a new rule also needs an entry there.
- `docs/specs/`: durable design records.

## Working here

- Source changes go through `aaaav-do` with an Alignment and Reality anchor before the first production edit.
- Keep the user-root layer thin: manage only behavior that is stable across projects and worth versioning. Machine credentials, login state, and project-specific workflows stay outside this repository.
- Installers never overwrite user files silently. A conflict fails unless `--force` is passed, which moves the old target to `~/.local/state/weihung-agent-root/backups/`, and uninstall restores what install replaced.
- Before committing, run the quick tests that assert the files you changed (`python3 tests/<name>.py`, `node --experimental-strip-types --test tests/<name>.mjs`). Run the end-to-end installer tests (`bash tests/install.sh`, `bash tests/uninstall.sh`, `tests/pi_fresh_machine.py`) only when the install or uninstall flow, the state file, or what gets written to the real home changes in substance; they take minutes, and a small change does not need them.
- After changing `pi/AGENTS.md.in` or `pi/herdr-agents-models.json`, run `bash scripts/install.sh` and reload pi. Change role models in `pi/herdr-agents-models.json`, not in the home config: an install stops when the home `models` was edited since the last install.

## Commits

- Use Conventional Commits: `type(scope): subject`, with types such as `feat`, `fix`, `refactor`, `chore`, `docs`, and `test`, and a scope such as `pi`, `install`, or `rules`. The subject may be English or Traditional Chinese.
- Commit messages contain no AI tool attribution: no `Co-Authored-By`, `Claude-Session`, or similar trailers, and no mention of AI tools.
- Stage files by name; never `git add .` or `git add -A`.
