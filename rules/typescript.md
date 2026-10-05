# TypeScript

- Prefer `interface` over `type` for object shapes. Use `type` for unions and intersections.
- No `any`. Use `unknown` + type guard when the type is genuinely dynamic.
- Prefer named exports. Default exports only for page/layout components.
