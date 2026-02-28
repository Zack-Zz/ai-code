---
inclusion: fileMatch
fileMatchPattern: ".*\\.(test|spec)\\.(js|jsx|ts|tsx|py|go|java)$"
---

# Test-Driven Development Workflow

This file is automatically included when working with test files.

## TDD Cycle (Red-Green-Refactor)

### 1. RED - Write Failing Test
Write a test that describes the expected behavior. The test should FAIL initially.

```typescript
// Example: Testing a user validation function
describe('validateUser', () => {
  it('should reject users without email', () => {
    const user = { name: 'John' };
    expect(() => validateUser(user)).toThrow('Email is required');
  });
});
```

### 2. GREEN - Minimal Implementation
Write just enough code to make the test pass.

```typescript
function validateUser(user) {
  if (!user.email) {
    throw new Error('Email is required');
  }
  return true;
}
```

### 3. REFACTOR - Improve Code
Clean up while keeping tests green.

## Required Test Coverage: 80%+

Check coverage with:
- JavaScript/TypeScript: `npm run test:coverage`
- Python: `pytest --cov`
- Go: `go test -cover ./...`
- Java: `mvn test jacoco:report`

## Edge Cases to Test

Always test these scenarios:
1. **Null/Undefined** input
2. **Empty** arrays/strings/objects
3. **Invalid types** (string when number expected)
4. **Boundary values** (0, -1, MAX_INT)
5. **Error conditions** (network failures, DB errors)
6. **Concurrent operations** (race conditions)
7. **Large datasets** (performance with 10k+ items)

## Test Structure

```typescript
describe('Feature/Component Name', () => {
  // Setup
  beforeEach(() => {
    // Initialize test data
  });

  // Teardown
  afterEach(() => {
    // Clean up
  });

  describe('Happy Path', () => {
    it('should handle valid input correctly', () => {
      // Arrange
      const input = createValidInput();
      
      // Act
      const result = functionUnderTest(input);
      
      // Assert
      expect(result).toBe(expectedOutput);
    });
  });

  describe('Edge Cases', () => {
    it('should handle null input', () => {
      expect(() => functionUnderTest(null)).toThrow();
    });

    it('should handle empty input', () => {
      expect(functionUnderTest([])).toEqual([]);
    });
  });

  describe('Error Handling', () => {
    it('should throw on invalid input', () => {
      expect(() => functionUnderTest('invalid')).toThrow('Invalid input');
    });
  });
});
```

## Mocking External Dependencies

Always mock external services (databases, APIs, file system):

```typescript
// Mock Supabase
jest.mock('@supabase/supabase-js', () => ({
  createClient: jest.fn(() => ({
    from: jest.fn(() => ({
      select: jest.fn().mockResolvedValue({ data: mockData, error: null })
    }))
  }))
}));

// Mock fetch
global.fetch = jest.fn(() =>
  Promise.resolve({
    json: () => Promise.resolve(mockResponse)
  })
);
```

## Test Anti-Patterns to Avoid

❌ **Don't test implementation details**
```typescript
// Bad: Testing internal state
expect(component.state.isLoading).toBe(true);

// Good: Testing behavior
expect(screen.getByText('Loading...')).toBeInTheDocument();
```

❌ **Don't share state between tests**
```typescript
// Bad: Tests depend on each other
let sharedUser;
it('creates user', () => { sharedUser = createUser(); });
it('updates user', () => { updateUser(sharedUser); });

// Good: Each test is independent
it('creates user', () => {
  const user = createUser();
  expect(user).toBeDefined();
});
```

❌ **Don't skip error paths**
```typescript
// Bad: Only testing happy path
it('fetches user', async () => {
  const user = await fetchUser(1);
  expect(user.name).toBe('John');
});

// Good: Test both success and failure
it('fetches user successfully', async () => {
  const user = await fetchUser(1);
  expect(user.name).toBe('John');
});

it('handles fetch error', async () => {
  await expect(fetchUser(999)).rejects.toThrow('User not found');
});
```

## Quality Checklist

Before committing:
- [ ] All new functions have unit tests
- [ ] All API endpoints have integration tests
- [ ] Critical user flows have E2E tests
- [ ] Edge cases are covered
- [ ] Error paths are tested
- [ ] External dependencies are mocked
- [ ] Tests are independent
- [ ] Coverage is 80%+

## Language-Specific Commands

### JavaScript/TypeScript
```bash
npm test                    # Run tests
npm run test:watch         # Watch mode
npm run test:coverage      # Coverage report
```

### Python
```bash
pytest                     # Run tests
pytest --cov              # Coverage report
pytest -v                 # Verbose output
```

### Go
```bash
go test ./...             # Run all tests
go test -cover ./...      # With coverage
go test -v ./...          # Verbose output
```

### Java
```bash
mvn test                  # Run tests
mvn test jacoco:report    # Coverage report
./gradlew test            # Gradle
```

## Resources

For more detailed patterns and examples, see:
- `skills/tdd-workflow/` - Comprehensive TDD methodology
- `skills/testing/` - Testing best practices per language
- `AGENTS.md` - tdd-guide agent guidelines
