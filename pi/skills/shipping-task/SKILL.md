---
name: shipping-task
description: Carry an approved task through the target app's branch or worktree, commit, pull request, and merge workflow.
---

# Shipping task

Read the target application's `AGENTS.md`, `CLAUDE.md`, and repository guidance before choosing its Git route. Use the app's branch naming, commit, test, review, and merge conventions. Keep the task's source changes and review evidence in that app's checkout.

1. Inspect `git status`, branch, remote, and the target app's shipping instructions. Create its required branch or worktree from the agreed base.
2. Implement and verify the task in that checkout. Stage only task files. Commit with the app's message convention and include no AI tool attribution.
3. Push the branch and create a pull request with `gh pr create`, using a body that states the change and verification. Record the PR URL.
4. Inspect CI and review results. Resolve failures or review findings in the same branch and update the PR.
5. Merge using the app's required method when its required gates pass. Verify the merged commit and clean up the task branch or worktree according to the app's convention.

Report local tests, remote CI, review, and merge as separate facts. Stop at an app-specific user approval gate when its instructions require that decision.
