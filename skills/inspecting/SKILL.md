---
name: inspecting
description: Use to check, audit, verify, or review a defined target.
---

# Inspecting

Define the evidence needed, check it, and give each scoped item a verdict.

For a branch, pull request, worktree, or change-set review, read
[DIFF-REVIEW.md](DIFF-REVIEW.md) first and use its fixed-point Standards/Spec
branch.

## Inspection Flow

### Phase 1: Scale the Inspection

Choose the lightest mode that can support a trustworthy conclusion:

- **Focused:** one narrow target or claim. Inspect it directly.
- **Standard:** several clear items. State a concise checklist, then proceed.
- **High-risk or ambiguous:** security, production, destructive effects, or unclear boundaries. Present the plan and wait for confirmation.

Include only dimensions relevant to the request: correctness, edge cases, architecture, security, performance, conventions, dependencies, and side effects.

### Phase 2: Verify

For each scoped item:

1. Identify the evidence that would prove or disprove it.
2. Gather that evidence directly. Invoke `investigating` only when the item requires substantial research or cross-source verification.
3. Record a verdict: pass, fail, needs attention, or insufficient evidence.
4. Keep observed facts separate from inference.

### Phase 3: Report

```
| Check Item | Verdict | Evidence / Notes |
|------------|---------|------------------|
| [item] | [verdict] | [evidence] |
```

Lead with the conclusion. Prioritize failures and recommended actions by impact. Name any unverified boundary instead of implying full coverage.

When another workflow supplies an artifact path, return verdicts to that phase's
artifact rather than creating a separate report.

## Principles

- **Evidence decides the verdict.** Confidence does not replace proof.
- **Scope is the completion criterion.** Finish when every scoped item has a verdict.
- **Depth follows risk.** Ceremony that does not improve the conclusion is noise.
