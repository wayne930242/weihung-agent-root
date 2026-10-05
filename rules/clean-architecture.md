# Clean Architecture

- Report these smells in code you touch instead of refactoring on sight: god object, circular dependency, wrong abstraction level, leaky abstraction, dead code.
- Apply the structure rules below only where the repository already follows them; otherwise match its existing patterns.

## Structure Rules

- One export per file for major components. Barrel files (index.ts) only at module boundaries.
- Dependency direction: handlers -> services -> repositories. Never reverse.
- Config at the edges. No hardcoded values in business logic.
- Error types per domain. No generic "Error" or string throws.
