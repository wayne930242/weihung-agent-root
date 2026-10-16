---
name: maintaining-pi-setup
description: Use when pi was updated (pi 更新了), when the user asks to check the extension system, align pinned packages or forks with upstream (對齊上游), or maintain the agent system (agent system 維護).
---

# Maintaining the Pi Setup

Bring `~/projects/weihung-agent-root` back in line with the installed pi and with each package's upstream. Every finding ends as a fix in this run, a decision put to the user, or a named follow-up; a check that only reports "differs" is not done. Source edits follow `aaaav-do`.

## Workflow

1. **Measure the gap.** Compare `pi --version` with the `@earendil-works/pi-coding-agent` devDependency in `package.json`; the devDependency marks the last version this repository was aligned to. Read the installed changelog between the two:
   `awk '/^## \[<aligned>\]/{exit} {print}' "$(npm root -g)/@earendil-works/pi-coding-agent/CHANGELOG.md"`, then its `Breaking Changes`, `Removed`, and `Changed` sections.
   - **Completion Criterion**: every breaking or extension-facing entry is listed with the API, event, or setting it touches.
2. **Find who is hit.** Search each touched API in `pi/extensions/` and in the installed packages under `~/.pi/agent/npm/node_modules/` and `~/.pi/agent/git/`, with `--exclude-dir=node_modules`. A clean `pi --mode rpc` load does not prove compatibility: a changed event shape fails only when the event fires.
   - Our extension: write a test that sends the new shape, see it fail, then fix it.
   - A fork we pin: fix it on the fork branch (step 5).
   - Any other package: check whether its latest release already handles it; otherwise name it as a follow-up.
   - **Completion Criterion**: every hit is fixed, scheduled through a newer pin, or reported with file and line.
3. **Retarget the types.** Set the devDependency to the installed version, run `npm install --no-package-lock` (the repository tracks no lockfile), then `npx tsc -p .` and the tests that cover the changed extensions.
   - **Completion Criterion**: `tsc` exits 0 against the new types.
4. **Bump the npm pins.** Run `python3 scripts/pi-pins.py outdated`, then `bump <name>` for each that differs. `pi-herdr-agents` and `pi-herdr-roles` also need `agents/` re-derived and `skills/orchestrate` compared, as `bump` prints.
   - **Completion Criterion**: `outdated` reports only the pins deliberately held, each with its reason.
5. **Align the forks.** `FORK_BRANCHES` in `scripts/pi-pins.py` lists them, and the comments in `scripts/pi_root/pins.py` name the upstream PRs each one carries. For each fork:
   - Check its PRs with `gh pr view <n> -R <upstream>`. When upstream has released all of them, return to the npm release as the `pins.py` comment describes.
   - Measure drift with `gh api repos/<fork>/compare/<upstream-owner>:main...<fork-branch> --jq '{ahead:.ahead_by,behind:.behind_by}'`. When `behind` is not 0, ask the user whether to merge or rebase; a rebase needs a force push, which requires their explicit confirmation.
   - Merge in a temporary `git worktree` from the local clone, because existing clones hold other work in progress. Resolve conflicts by carrying the fork's own changes to wherever upstream moved that content.
   - Run the fork's tests before and after the merge in the same directory and compare the failing test names. A worktree under `$TMPDIR` fails path assertions because `/var` resolves to `/private/var`, so only new failures count, and a new failure that passes when rerun on its own is a flake.
   - Push the fork branch normally, delete the temporary worktree and branch with `git branch -d`, then run `python3 scripts/pi-pins.py bump <fork name>` and update the fork notes in `pins.py` and `README.md`.
   - **Completion Criterion**: each fork shows `behind: 0`, or the user chose to hold it.
6. **Check the scheduled update.** Read the tail of `~/.local/state/weihung-agent-root/pi-autoupdate.log`. Repeated `Skipped:` lines mean `auto` has not run since the first of them; remove the cause, such as untracked machine-local state that belongs in `.gitignore`.
   - **Completion Criterion**: nothing in the repository blocks the next `auto` run.
7. **Install and verify.** Run `bash scripts/install.sh`, then load pi once:
   `echo '{"id":"s","type":"get_commands"}' | pi --mode rpc --no-session --offline --no-approve` from `~/.local/state/weihung-agent-root`. The load must exit 0 with a successful response. Ask the user to `/reload` their running sessions.
   - **Completion Criterion**: install and the load both pass.
8. **Retire stale lessons.** Search memory for every issue number and behavior that the changelog says is fixed (for example, `memory_search` for `5581`). Report each entry that the fix makes obsolete, then remove it with `memory_forget` once the user agrees.
   - **Completion Criterion**: each matching entry is removed, kept for a stated reason, or awaiting the user's decision.

Commit by concern (extension fix, pin bumps, fork pin, this skill) and follow this repository's `AGENTS.md`.
