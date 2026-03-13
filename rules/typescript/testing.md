---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---
# TypeScript/JavaScript Testing

> This file extends [common/testing.md](../common/testing.md) with TypeScript/JavaScript specific content.

## E2E Testing

Use **Playwright** as the E2E testing framework for critical user flows.

## Unit and Integration Testing

- Prefer colocated or clearly discoverable test files such as `foo.test.ts` or `foo.spec.ts`
- Test exported business logic, parsers, mappers, and boundary validation directly
- Add integration tests for API handlers, persistence adapters, and hook/script behavior
- When fixing bugs, add the reproducing test before changing implementation

## TypeScript-Specific Expectations

- Test runtime validation, not just compile-time typing
- Cover nullish, malformed, and partial external data shapes
- Verify type-driven boundary behavior such as DTO mapping and narrowing-sensitive branches
- Prefer deterministic tests over snapshot-heavy coverage for domain logic

## Agent Support

- **e2e-runner** - Playwright E2E testing specialist
