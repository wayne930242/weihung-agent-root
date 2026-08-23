---
name: tdd
description: Use for every programming change.
---

# Test-Driven Development

Own the correctness feedback loop within `leveraging-tasks`. Every programming
change uses this discipline; documentation-only work remains agent-reviewed
outside TDD.

## 1. Separate correctness from appropriateness

**Correctness is agent-owned.** For each criterion, choose the smallest credible
interface that exercises the real behavior and can go red before the change:

- a deterministic test at the highest stable public seam
- the project's CLI, API, runtime harness, telemetry, or operational interface
- the actual user-facing surface through Chrome or browser automation, computer
  use, or another available interface

Prefer the interface closest to real use when a lower seam would give false
confidence. For browser-facing behavior, exercise the available Chrome or
browser-automation path; use the non-authenticated path first unless the scenario
requires authentication. Existing tests, types, contracts, and invariants may
establish coverage, but a behavior change still needs red-capable feedback.

**Appropriateness is human-owned** only when the unresolved question is whether
the objectively working result is suitable for its users or context: UX feel,
clarity, usefulness, workflow fit, or domain judgment. Read
[HUMAN-FINAL-CHECK.md](HUMAN-FINAL-CHECK.md) for that branch. The agent completes
the available correctness checks before the checkpoint; a human verdict never
stands in for correctness evidence.

Record both boundaries in `design.md`: how the agent will prove correctness and,
when needed, what appropriateness question the user will judge.

**Complete when:** every programming criterion has a red-capable agent-operated
interface, and any human-owned appropriateness question is separate and explicit.

## 2. Run vertical slices

For an observable behavior change:

1. **Red:** establish one reproducible failing check or observation through the
   selected interface and prove it fails for the expected reason.
2. **Green:** implement only enough behavior to make that check pass.
3. Re-run the focused check, the affected suite, and the closest practical
   user-facing interface.
4. Repeat with the next behavior learned from the previous slice.

For a behavior-preserving refactor, establish or confirm characterization
coverage first, keep it green through each slice, then re-run the closest
practical interface after the refactor.

Expected values come from the spec, a worked example, or another independent
source. Checks observe public behavior rather than private methods, internal call
counts, or a side channel that bypasses the real interface.

**Complete when:** every programming criterion has agent-operated correctness
evidence through its agreed seam and no programming result is left unverified.

## 3. Return evidence

Report automated results, interface observations, operational evidence, and gaps
to the caller's `verification.md`. Record a human final-check verdict separately
as appropriateness evidence. A pending appropriateness checkpoint leaves that
product decision open even when correctness checks pass; a missing correctness
result remains an implementation gap.

---

Adapted from [mattpocock/skills](https://github.com/mattpocock/skills) `tdd`
(MIT License, Copyright (c) 2026 Matt Pocock).
