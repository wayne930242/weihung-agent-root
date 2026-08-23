---
---

# Git Safety

- Force push to any remote branch requires explicit user confirmation before executing — state the exact command and target and wait for approval before running.
- Before staging untracked files, separate generated local state from project artifacts. Phased artifacts under `docs/specs/` are project artifacts; machine-local `Plans/`, `MEMORY/`, and analysis snapshots are not. Stage specific files by name; never use `git add .` or `git add -A`.
