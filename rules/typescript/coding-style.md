---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---
# TypeScript/JavaScript Coding Style

> This file extends [common/coding-style.md](../common/coding-style.md) with TypeScript/JavaScript specific content.

## Type Safety

- In TypeScript projects, require `strict` mode for production code
- In TypeScript projects, prefer enabling `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, and `noImplicitOverride`
- Avoid `any`; if unavoidable, isolate it at boundaries and document why
- In TypeScript files, add explicit return types for exported functions and shared utilities
- In TypeScript files, prefer literal unions over `enum` unless runtime enum behavior is required
- In TypeScript files, avoid double assertions such as `as unknown as Foo`

## Immutability

Use spread operator for immutable updates:

```typescript
// WRONG: Mutation
function updateUser(user, name) {
  user.name = name  // MUTATION!
  return user
}

// CORRECT: Immutability
function updateUser(user, name) {
  return {
    ...user,
    name
  }
}
```

## Error Handling

Use async/await with try-catch:

```typescript
try {
  const result = await riskyOperation()
  return result
} catch (error) {
  console.error('Operation failed:', error)
  throw new Error('Detailed user-friendly message')
}
```

- Do not silently fire-and-forget async work in production paths
- Convert unknown errors into safe user-facing messages at boundaries
- Keep internal error details in logs, not in UI responses

## Types and Interfaces

- In TypeScript files, use `interface` for object-shaped contracts that may be extended or implemented
- In TypeScript files, use `type` for unions, mapped types, utility-type composition, and function signatures
- Keep shared DTOs and domain types explicit; do not pass raw external payloads through the app unchanged
- In TypeScript files, type component props, hook params, and hook return values explicitly when exported or shared

## Naming and Structure

- Use `PascalCase` for React components and exported classes
- Use `camelCase` for functions, variables, hooks, and utility modules
- Prefix custom hooks with `use`
- Keep one primary responsibility per file; split unrelated helpers out instead of growing files indefinitely
- Prefer feature-oriented directories over folders grouped only by technical type

## React and UI

- In TypeScript files, type all component props explicitly
- Keep hooks at the top level and avoid conditional hook calls
- Keep presentation components free of API/storage details; map external data before rendering
- Prefer pure transforms for derived UI state instead of mutating intermediate objects

## Input Validation

Use Zod for schema-based validation:

```typescript
import { z } from 'zod'

const schema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(150)
})

const validated = schema.parse(input)
```

- Validate all external input at the boundary: HTTP, CLI, file, storage, and LLM/tool payloads
- In TypeScript files, parse unknown data into typed application objects before use
- Do not rely on TypeScript types alone for runtime safety

## Console.log

- No `console.log` statements in production code
- Use proper logging libraries instead
- See hooks for automatic detection
