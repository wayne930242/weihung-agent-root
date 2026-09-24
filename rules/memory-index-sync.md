---
---

# Memory Index Sync

When writing or updating any file under `memory/`, MUST update the corresponding one-liner in `memory/MEMORY.md` in the same action.

- The index is the only memory content loaded automatically at session start
- A stale index one-liner overrides a correctly updated file — the file content is never read unless the index triggers it
- One-liner MUST reflect current file content, not the previous content
