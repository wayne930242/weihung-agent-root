---
---

# Git Safety

- Force push to any remote branch requires explicit user confirmation before executing — state the exact command and target and wait for approval before running.
- Before staging untracked files, verify `.gitignore` excludes local tooling directories (openspec/, Plans/, MEMORY/, docs/agent-system/). Stage specific files by name; never use `git add .` or `git add -A`.
