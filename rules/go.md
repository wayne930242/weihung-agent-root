# Go

- Combine all changes (imports + code) into a single edit. Never leave an intermediate state with unused imports.
- Use error wrapping with `fmt.Errorf("context: %w", err)`, not bare returns.
- Prefer table-driven tests. No test helpers that hide assertions.
