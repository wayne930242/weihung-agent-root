# Working Style

IMPORTANT: When the user describes an architecture or approach, follow their direction. Ask questions instead of proposing alternatives.

- When you spot poor architecture, immediately suggest refactoring. Do not silently work around it.
- Read before write. Read any file before modifying it. Understand existing patterns first.
- Do only what is asked. No unsolicited docstrings, no drive-by refactoring, no unrelated improvements.

# Architecture Principles

- Prefer composition over inheritance, explicit dependencies over implicit coupling, fail-fast over silent degradation.
- Functions do one thing. Organize files by domain, not by file type.
- Do not design for hypothetical requirements. Three duplicate lines beat a premature abstraction.

# Quality Baseline

- No TODOs, no stubs, no mocks in delivered code. Start it, finish it.
- Run tests before deploying. Verify destructive deploy commands carefully before using them.
- Commit messages must not mention AI tools.
