# Working Style

IMPORTANT: When the user describes an architecture or approach, follow their direction. Ask questions instead of proposing alternatives.

- When you spot poor architecture, immediately suggest refactoring. Do not silently work around it.
- Read before write. Read any file before modifying it. Understand existing patterns first.
- Do only what is asked. No unsolicited docstrings, no drive-by refactoring, no unrelated improvements.

# Simplicity First

Minimum code that solves the problem. Nothing speculative.

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

# Surgical Changes

Touch only what you must. Clean up only your own mess.

When editing existing code:
- Don't improve adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

Every changed line should trace directly to the user's request.

# Architecture Principles

- Prefer composition over inheritance, explicit dependencies over implicit coupling, fail-fast over silent degradation.
- Functions do one thing. Organize files by domain, not by file type.
- Do not design for hypothetical requirements. Three duplicate lines beat a premature abstraction.

# Goal-Driven Execution

Transform tasks into verifiable goals before starting.

- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

# Quality Baseline

- No TODOs, no stubs, no mocks in delivered code. Start it, finish it.
- Run tests before deploying. Verify destructive deploy commands carefully before using them.
- Commit messages must not mention AI tools.
