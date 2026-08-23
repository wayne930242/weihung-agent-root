---
name: domain-modeling
description: Use when project terminology or domain boundaries need refinement.
---

# Domain Modeling

Actively reconcile the user's language, the project's glossary, and code. Direct
source-changing requests enter `leveraging-tasks`; return confirmed terms and
decisions to its Requirements or Design phase.

## Discipline

1. Read the applicable `CONTEXT.md`; follow `CONTEXT-MAP.md` when the repository
   has multiple domain contexts.
2. Surface conflicts between the user's term, glossary definition, and code.
   Sharpen vague or overloaded terms into one canonical meaning.
3. Stress-test relationships and boundaries with concrete edge-case scenarios.
4. Check asserted behavior against code. Let the user decide when current code
   and intended domain truth disagree.
5. Record a confirmed term immediately in `CONTEXT.md`, using
   [CONTEXT-FORMAT.md](../grill-with-docs/CONTEXT-FORMAT.md). Keep the glossary
   free of implementation detail.
6. Offer an ADR using [ADR-FORMAT.md](../grill-with-docs/ADR-FORMAT.md) only when
   the decision is hard to reverse, surprising without context, and produced by
   a real trade-off.

## Carry the model into code

- Use the confirmed ubiquitous language in identifiers, tests, errors, and
  public contracts within its bounded context.
- Keep domain invariants in the domain model. UI, transport, persistence, and
  orchestration layers call the model instead of reimplementing its rules.
- Translate external schemas, persistence records, and another context's
  vocabulary at explicit adapter seams; do not let them become the internal
  domain model by accident.
- Use tactical DDD patterns only when they clarify real domain rules. Do not
  manufacture entities, aggregates, value objects, or repositories as ceremony.
- Return to Requirements or Design when implementation reveals a domain
  contradiction. Do not encode an unconfirmed model silently.

Verification checks code and test vocabulary, invariant placement, context
boundaries, and adapter translations against the confirmed model.

Create the glossary or ADR directory only when there is confirmed knowledge to
record. Domain modeling is complete when language, boundaries, invariants,
adapters, code, and tests express the same confirmed model.

---

Adapted from [mattpocock/skills](https://github.com/mattpocock/skills)
`domain-modeling` (MIT License, Copyright (c) 2026 Matt Pocock).
