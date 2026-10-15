---
description: "Agents do not use git stash"
condition: '\bgit\s+stash\b'
scope: "tool:bash"
repeatMode: after-gap
repeatGap: 1
---

Do not use `git stash`: a stash entry outlives the run, and Safety Net blocks `git stash drop`, so it stays behind for the user to clean up.

To prove a test fails without a change, copy the changed file to `/tmp` and restore it afterwards, or run `git show HEAD:<path> > <path>` and put your version back. To set work aside, commit it on a branch.
