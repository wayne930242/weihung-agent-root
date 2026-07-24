---
name: grill-with-docs
description: A relentless interview to sharpen a plan or design, recording decisions as ADRs and domain terms in CONTEXT.md as they crystallise.
disable-model-invocation: true
---

# Grill With Docs

Run a `/grilling` session.
As the interview resolves terms and decisions, capture them the moment they crystallise — docs are written during the session, never batched to the end.

## During the session

- **Challenge against the glossary.** When the user uses a term that conflicts with the existing language in `CONTEXT.md`, call it out immediately.
- **Sharpen fuzzy language.** When a term is vague or overloaded, propose a precise canonical term.
- **Discuss concrete scenarios.** Stress-test domain relationships with edge-case scenarios that force precise boundaries between concepts.
- **Cross-reference with code.** When the user states how something works, check whether the code agrees; surface contradictions.
- **Update CONTEXT.md inline.** When a term is resolved, record it right away using [CONTEXT-FORMAT.md](./CONTEXT-FORMAT.md).
  `CONTEXT.md` is a glossary and nothing else — keep it devoid of implementation details.
- **Offer ADRs sparingly.** Offer one only when the decision is hard to reverse, surprising without context, AND the result of a real trade-off.
  Use [ADR-FORMAT.md](./ADR-FORMAT.md).

Create files lazily — `CONTEXT.md` when the first term is resolved, `docs/adr/` when the first ADR is needed.

## Handoff

When shared understanding is reached and the work heads to implementation, synthesise it into an OpenSpec change (`opsx:propose`) rather than re-interviewing.

---

Ported and adapted from [mattpocock/skills](https://github.com/mattpocock/skills) `grill-with-docs` + `domain-modeling` (MIT License, Copyright (c) 2026 Matt Pocock).
Adaptation: domain-modeling duties folded in; handoff targets OpenSpec.
