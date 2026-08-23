---
name: investigating
description: Use to research a question or claim with traceable evidence.
---

# Investigating

1. Define the exact question and completion boundary.
2. Gather relevant evidence:
   - code: use codebase-memory graph tools first; use text search for prose,
     configuration, and literals; check history when behavior changed over time
   - external facts: current primary sources, official documentation, source
     code, specifications, or first-party APIs
   - runtime: reproducible commands, logs, errors, and test output
3. Cross-check material claims and resolve source conflicts.
4. Separate confirmed facts, supported inference, and unknowns.
5. Report the reasoning chain with a source beside each material claim.

When another workflow supplies an artifact path, return evidence in the shape
that phase needs. Do not create a parallel plan or specification.

**Complete when:** the scoped question is answered or the missing evidence is
named precisely.
