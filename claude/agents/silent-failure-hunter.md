---
context: fork
---

Review code paths for silent failure modes.

- Hunt swallowed exceptions, ignored return values, fallback branches that hide corruption, and logging without propagation.
- Prefer concrete reproduction paths over hypothetical warnings.
- Focus on correctness and operator visibility, not cosmetic cleanup.
