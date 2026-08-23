---
name: assuring-quality
description: Use for final QA before release.
---

# Assuring Quality

Own final exploratory QA and its evidence. Use an active Mini SDD
`verification.md` as the findings ledger; otherwise reuse the project's QA
convention or create `docs/qa/discover-qa-YYYY-MM-DD.md` when findings must
persist.

## 1. Discover

Record the scope, version or branch, environment, primary flows, and every
unexpected behavior with reproduction steps. Cover only relevant edges such as
errors, boundaries, concurrency, permissions, and data consistency.

**Complete when:** the declared scope was exercised and every observation is in
the ledger.

## 2. Resolve

For each finding:

1. Trace the symptom to a falsifiable root-cause hypothesis.
2. Hand any source-changing fix to `leveraging-tasks` with the finding and repro
   as its requirements input.
3. Re-run the repro and affected suite after the fix.
4. Record the evidence or unresolved gap before moving to the next finding.

Git commits are delivery evidence, not a QA phase requirement. Do not create or
push one unless separately authorized by the active workflow.

## 3. Close

Report discovered, resolved, and deferred findings with their evidence and
owner. Final QA passes only when no unresolved finding contradicts the release
criteria.
