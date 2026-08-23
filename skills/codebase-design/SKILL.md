---
name: codebase-design
description: Use when designing or changing module interfaces and seams.
---

# Codebase Design

Supply design discipline within `leveraging-tasks`. Direct source-changing
requests enter that lifecycle first; return decisions to its `design.md`.

## Vocabulary

- **Module:** an interface plus its implementation, at any scale.
- **Interface:** everything a caller must know, including invariants, ordering,
  errors, configuration, and performance characteristics.
- **Depth:** useful behavior delivered per unit of interface burden.
- **Seam:** where behavior can vary without editing the caller.
- **Adapter:** a concrete implementation occupying a seam.
- **Leverage:** capability reused by callers through a small interface.
- **Locality:** change, knowledge, bugs, and proof concentrated behind that
  interface.

Use these terms consistently in the design artifact.

`domain-modeling` owns semantic meaning, ubiquitous language, contexts, and
invariants. This skill owns the interface and seam shape that contains them.

## Design checks

1. Place the seam at an existing architectural boundary when it fits; introduce
   a new seam only for real variation. One adapter is usually hypothetical; two
   adapters demonstrate variation.
2. Minimize what callers must know. Hide invariants and workflow complexity
   behind the interface instead of distributing them across call sites.
3. Apply the deletion test: removing a useful module should redistribute its
   complexity to callers. If complexity disappears, the module is probably a
   pass-through.
4. Make the public interface the primary test surface. Accept varying
   dependencies and return observable results where that creates a stable seam.
5. Compare at least two interface shapes when no clear precedent exists and the
   choice is surprising or costly to reverse. Evaluate depth, locality,
   compatibility, and testability; present user-owned trade-offs for confirmation.

**Complete when:** `design.md` names the chosen interface and seam, the precedent
or alternatives considered, caller burden, adapters, and verification surface.

---

Adapted from [mattpocock/skills](https://github.com/mattpocock/skills)
`codebase-design` (MIT License, Copyright (c) 2026 Matt Pocock).
