---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---
# TypeScript/JavaScript Comments and JSDoc

> This file extends [common/coding-style.md](../common/coding-style.md) with TypeScript/JavaScript specific comment guidance.

## General Rules

- Comments should explain intent, constraints, tradeoffs, or non-obvious behavior
- Do not add comments that simply restate the code line-by-line
- Prefer deleting stale comments over keeping misleading documentation
- Keep comments short and local unless the code truly needs a larger explanation

## JSDoc / TSDoc

- Add JSDoc for exported functions, shared hooks, public classes, and non-trivial public types
- Document input constraints, return values, and important side effects
- Document thrown errors when callers need to handle them explicitly
- Keep examples small and aligned with real usage

## When Comments Are Required

- Complex parsing logic
- Non-obvious regular expressions
- Security-sensitive branches and validation assumptions
- Workarounds for framework/tooling limitations
- Performance-sensitive code where the chosen approach is not obvious

## TODO / FIXME Rules

- `TODO` and `FIXME` must include useful context
- Prefer linking to an issue, task ID, or a concrete follow-up condition
- Remove resolved TODO/FIXME comments promptly

## Discouraged Patterns

- Noisy comments such as "increment counter" or "assign value"
- Large banner comments that do not add operational value
- Commented-out code left in production files
- Misleading "temporary" comments with no owner or follow-up path
