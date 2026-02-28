---
inclusion: always
---

# Coding Standards

Core coding principles for this workspace.

## Immutability (CRITICAL)

Always create new objects, never mutate existing ones.

```typescript
// ❌ BAD: Mutation
const user = { name: 'John', age: 30 };
user.age = 31; // Mutates original

// ✅ GOOD: Immutable update
const user = { name: 'John', age: 30 };
const updatedUser = { ...user, age: 31 }; // New object
```

```python
# ❌ BAD: Mutation
users = [{'name': 'John'}]
users[0]['age'] = 30  # Mutates original

# ✅ GOOD: Immutable update
users = [{'name': 'John'}]
updated_users = [{**user, 'age': 30} for user in users]
```

## File Organization

- **Many small files** over few large ones
- **200-400 lines** typical, **800 lines maximum**
- Organize by **feature/domain**, not by type
- High cohesion, low coupling

```
# ❌ BAD: Organized by type
src/
  components/
  services/
  utils/

# ✅ GOOD: Organized by feature
src/
  auth/
    LoginForm.tsx
    authService.ts
    authUtils.ts
  users/
    UserProfile.tsx
    userService.ts
    userUtils.ts
```

## Function Size

- Functions should be **< 50 lines**
- Single responsibility principle
- Extract complex logic into helper functions

```typescript
// ❌ BAD: Large function doing too much
function processOrder(order) {
  // 100+ lines of validation, calculation, DB operations...
}

// ✅ GOOD: Small, focused functions
function processOrder(order) {
  validateOrder(order);
  const total = calculateTotal(order);
  const discount = applyDiscount(total, order.coupon);
  return saveOrder({ ...order, total: discount });
}
```

## Error Handling

Handle errors at every level:

```typescript
// ✅ GOOD: Comprehensive error handling
async function fetchUser(id: string) {
  try {
    const response = await fetch(`/api/users/${id}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const user = await response.json();
    
    if (!user) {
      throw new Error('User not found');
    }
    
    return user;
  } catch (error) {
    // Log detailed context server-side
    console.error('Failed to fetch user:', { id, error });
    
    // Throw user-friendly message
    throw new Error('Unable to load user profile. Please try again.');
  }
}
```

## Input Validation

Validate all user input at system boundaries:

```typescript
import { z } from 'zod';

// Define schema
const UserSchema = z.object({
  email: z.string().email(),
  age: z.number().min(0).max(150),
  name: z.string().min(1).max(100)
});

// Validate input
function createUser(input: unknown) {
  const validated = UserSchema.parse(input); // Throws if invalid
  return saveUser(validated);
}
```

## Code Quality Checklist

Before committing:
- [ ] Functions are small (< 50 lines)
- [ ] Files are focused (< 800 lines)
- [ ] No deep nesting (> 4 levels)
- [ ] Proper error handling
- [ ] No hardcoded values (use constants/config)
- [ ] Readable, well-named identifiers
- [ ] No commented-out code
- [ ] No console.log in production code

## Naming Conventions

### Variables & Functions
- Use descriptive names: `getUserById` not `get`
- Boolean variables: `isActive`, `hasPermission`, `canEdit`
- Arrays: plural names `users`, `orders`, `items`

### Constants
- UPPER_SNAKE_CASE for true constants
- camelCase for configuration objects

```typescript
// Constants
const MAX_RETRY_ATTEMPTS = 3;
const API_BASE_URL = 'https://api.example.com';

// Configuration
const apiConfig = {
  timeout: 5000,
  retries: 3
};
```

### Classes & Types
- PascalCase: `UserProfile`, `OrderService`
- Interfaces: `IUserRepository` or `UserRepository`
- Types: `UserData`, `OrderStatus`

## Comments

- Write self-documenting code (good names > comments)
- Comment **why**, not **what**
- Use JSDoc/docstrings for public APIs

```typescript
// ❌ BAD: Obvious comment
// Increment counter by 1
counter++;

// ✅ GOOD: Explains why
// Retry count must be incremented before the delay to prevent
// infinite loops when the server returns 429 Too Many Requests
retryCount++;
await delay(retryCount * 1000);
```

## Performance Considerations

- Avoid premature optimization
- Profile before optimizing
- Use appropriate data structures
- Cache expensive computations
- Lazy load when possible

## Language-Specific Standards

For language-specific guidelines, see:
- `skills/coding-standards/` - Detailed standards per language
- `.kiro/steering/multi-language-workflow.md` - Language-specific commands
