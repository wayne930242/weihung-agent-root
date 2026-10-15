---
description: "Agents stage files by name"
condition: '\bgit\s+add\b[^\n;&|]*\s(-A|--all|\.)(?=\s|$|[;&|])'
scope: "tool:bash"
repeatMode: after-gap
repeatGap: 1
---

Do not stage with `git add -A`, `git add --all`, or `git add .`: they pick up machine-local state such as plans, memory, scratch files, and other workers' changes.

Stage each file by name: `git add path/to/a.ts path/to/b.ts`.
