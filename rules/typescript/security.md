---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---
# TypeScript/JavaScript Security

> This file extends [common/security.md](../common/security.md) with TypeScript/JavaScript specific content.

## Secret Management

```typescript
// NEVER: Hardcoded secrets
const apiKey = "sk-proj-xxxxx"

// ALWAYS: Environment variables
const apiKey = process.env.OPENAI_API_KEY

if (!apiKey) {
  throw new Error('OPENAI_API_KEY not configured')
}
```

## Boundary Safety

- Treat all external data as `unknown` until validated
- Validate request bodies, query params, file content, env vars, and tool payloads at entry points
- Do not trust TypeScript annotations as runtime protection

## Error and Data Exposure

- Do not return stack traces, ORM errors, or raw third-party responses to clients
- Redact sensitive fields before logging objects
- Keep auth, rate limiting, and authorization checks close to request boundaries

## Dependency and Execution Safety

- Prefer parameter arrays over shell strings when executing subprocesses
- Avoid dynamic code execution and unchecked template interpolation into commands
- Keep package-manager, build, and tool execution behind validated allowlists

## Agent Support

- Use **security-reviewer** skill for comprehensive security audits
