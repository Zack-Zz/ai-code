---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---
# TypeScript/JavaScript Patterns

> This file extends [common/patterns.md](../common/patterns.md) with TypeScript/JavaScript specific content.

## API Response Format

```typescript
interface ApiResponse<T> {
  success: boolean
  data?: T
  error?: string
  meta?: {
    total: number
    page: number
    limit: number
  }
}
```

- Keep transport envelopes stable across endpoints
- Separate transport DTOs from domain models when the shapes differ
- Do not leak internal error objects or stack traces in API responses

## Custom Hooks Pattern

```typescript
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState<T>(value)

  useEffect(() => {
    const handler = setTimeout(() => setDebouncedValue(value), delay)
    return () => clearTimeout(handler)
  }, [value, delay])

  return debouncedValue
}
```

- Keep hooks focused on one concern
- Return stable, well-typed values
- Avoid mixing data fetching, storage mutation, and presentational state in a single hook

## Repository Pattern

```typescript
interface Repository<T> {
  findAll(filters?: Filters): Promise<T[]>
  findById(id: string): Promise<T | null>
  create(data: CreateDto): Promise<T>
  update(id: string, data: UpdateDto): Promise<T>
  delete(id: string): Promise<void>
}
```

- Keep business logic dependent on repository interfaces rather than storage implementations
- Map storage records into domain types before returning them to application code

## Service Boundary Pattern

```typescript
export async function createUser(input: unknown): Promise<UserDto> {
  const parsed = CreateUserSchema.parse(input)
  const user = await userRepository.create(parsed)
  return toUserDto(user)
}
```

- Parse `unknown` inputs at service boundaries
- Return stable DTOs from service functions
- Avoid passing ORM models, database rows, or third-party payloads directly into UI code

## Async Workflow Pattern

```typescript
export async function processOrder(orderId: string): Promise<Result> {
  const order = await orderRepository.findById(orderId)
  if (!order) throw new Error('Order not found')

  const payment = await paymentService.capture(order)
  return buildResult(order, payment)
}
```

- Make async sequencing explicit
- Avoid hidden side effects inside utility helpers
- Isolate retries, timeouts, and external IO behind named functions or services
