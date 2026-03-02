---
name: java-coding-standards
description: "Java coding standards for Spring Boot services: naming, immutability, Javadoc conventions, Optional usage, streams, exceptions, generics, and project layout."
origin: ai-code
---

# Java Coding Standards

Standards for readable, maintainable Java (17+) code in Spring Boot services.

## When to Activate

- Writing or reviewing Java code in Spring Boot projects
- Enforcing naming, immutability, or exception handling conventions
- Working with records, sealed classes, or pattern matching (Java 17+)
- Reviewing use of Optional, streams, or generics
- Structuring packages and project layout

## Core Principles

- Prefer clarity over cleverness
- Immutable by default; minimize shared mutable state
- Fail fast with meaningful exceptions
- Consistent naming and package structure

## Naming

```java
// ✅ Classes/Records: PascalCase
public class MarketService {}
public record Money(BigDecimal amount, Currency currency) {}

// ✅ Methods/fields: camelCase
private final MarketRepository marketRepository;
public Market findBySlug(String slug) {}

// ✅ Constants: UPPER_SNAKE_CASE
private static final int MAX_PAGE_SIZE = 100;
```

## Documentation Comments (Javadoc)

- Public classes/interfaces/enums/records must have class-level Javadoc.
- Class Javadoc should describe business purpose and responsibility, not implementation details.
- Include `@author` and `@since` for public top-level types.
- Public/protected methods must have Javadoc when behavior is non-trivial, has side effects, or throws domain exceptions.
- Public constants must have Javadoc when meaning is not obvious from the name alone.
- Private methods/getters/setters do not require Javadoc unless logic is complex.

```java
/**
 * Application service for market lifecycle operations.
 * Coordinates validation, persistence, and domain events.
 *
 * @author ai-code
 * @since 1.0.0
 */
public class MarketService {

  /**
   * Maximum number of records allowed in a single query page.
   */
  public static final int MAX_PAGE_SIZE = 100;

  /**
   * Creates a market and persists it atomically.
   *
   * @param request validated market creation request
   * @return persisted market aggregate
   * @throws MarketAlreadyExistsException when a market with the same slug already exists
   */
  public Market createMarket(CreateMarketRequest request) { ... }
}
```

### Javadoc Tag Rules

- `@param`: required for each parameter in documented methods/constructors.
- `@return`: required when return value is not `void`; describe business meaning.
- `@throws`: required for checked exceptions and meaningful domain/runtime exceptions.
- `@since`: required on public top-level types and public APIs introduced in new versions.
- `@author`: required on public top-level types (use team/org identifier, not personal PII).
- `@implNote`/`@apiNote`: use when callers must know behavior contracts or extension constraints.

### Javadoc Quality Rules

- Do not repeat the method name literally (avoid low-value comments).
- Describe intent, constraints, and side effects.
- Keep comments in sync with code changes; stale comments are bugs.
- Prefer English for API/Javadoc consistency unless project rules require otherwise.

## Immutability

```java
// ✅ Favor records and final fields
public record MarketDto(Long id, String name, MarketStatus status) {}

public class Market {
  private final Long id;
  private final String name;
  // getters only, no setters
}
```

## Optional Usage

```java
// ✅ Return Optional from find* methods
Optional<Market> market = marketRepository.findBySlug(slug);

// ✅ Map/flatMap instead of get()
return market
    .map(MarketResponse::from)
    .orElseThrow(() -> new EntityNotFoundException("Market not found"));
```

## Streams Best Practices

```java
// ✅ Use streams for transformations, keep pipelines short
List<String> names = markets.stream()
    .map(Market::name)
    .filter(Objects::nonNull)
    .toList();

// ❌ Avoid complex nested streams; prefer loops for clarity
```

## Exceptions

- Use unchecked exceptions for domain errors; wrap technical exceptions with context
- Create domain-specific exceptions (e.g., `MarketNotFoundException`)
- Avoid broad `catch (Exception ex)` unless rethrowing/logging centrally

```java
throw new MarketNotFoundException(slug);
```

## Generics and Type Safety

- Avoid raw types; declare generic parameters
- Prefer bounded generics for reusable utilities

```java
public <T extends Identifiable> Map<Long, T> indexById(Collection<T> items) { ... }
```

## Project Structure (Maven/Gradle)

```
src/main/java/com/example/app/
  config/
  controller/
  service/
  repository/
  domain/
  dto/
  util/
src/main/resources/
  application.yml
src/test/java/... (mirrors main)
```

## Formatting and Style

- Use 2 or 4 spaces consistently (project standard)
- One public top-level type per file
- Keep methods short and focused; extract helpers
- Order members: constants, fields, constructors, public methods, protected, private

## Code Smells to Avoid

- Long parameter lists → use DTO/builders
- Deep nesting → early returns
- Magic numbers → named constants
- Static mutable state → prefer dependency injection
- Silent catch blocks → log and act or rethrow

## Logging

```java
private static final Logger log = LoggerFactory.getLogger(MarketService.class);
log.info("fetch_market slug={}", slug);
log.error("failed_fetch_market slug={}", slug, ex);
```

## Null Handling

- Accept `@Nullable` only when unavoidable; otherwise use `@NonNull`
- Use Bean Validation (`@NotNull`, `@NotBlank`) on inputs

## Testing Expectations

- JUnit 5 + AssertJ for fluent assertions
- Mockito for mocking; avoid partial mocks where possible
- Favor deterministic tests; no hidden sleeps

**Remember**: Keep code intentional, typed, and observable. Optimize for maintainability over micro-optimizations unless proven necessary.
