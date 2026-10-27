# Java construction, reuse and type placement

Required companion to [Java writing requirements](java.md) for affected Java work.

## Keep test construction inside the test class

Production constructors must serve real business modeling, actual dependency
injection or framework instantiation. Do not add a constructor, overload,
setter, factory, builder or configuration switch solely for a unit test.
Renaming it, reducing visibility or adding `@VisibleForTesting` does not give
it a production purpose. Do not weaken production validation to satisfy a test.

Build special data, mocks and substitutes inside the corresponding test class
and use existing normal construction/business entry points. Real production
dependency improvements may also help tests; establish that production purpose.
If normal construction rejects a state, first determine whether it is reachable.
Simulate genuinely reachable dirty/deserialized states inside the test class
with their real origin explained; do not manufacture invalid instances to
bypass the validation being tested. Test rejection through the normal entry.

Inside the test class, a local helper can reuse the production constructor:

```java
/**
 * Creates the amount required by this test case.
 *
 * @param cents amount for this case in minor currency units
 * @return an instance created through normal production validation
 */
private OrderAmount createAmount(long cents) {
    return new OrderAmount(cents);
}
```

An actual JPA/framework construction requirement is a production purpose, not
a test-only exemption. Use [JPA rules](jpa.md) only when the task involves that mechanism.

## Reuse existing implementations and consolidate the same rule

- Before adding an implementation, inspect relevant existing code in the current
  module and established shared components. Read its actual contract and callers;
  do not create another implementation merely because its name or location differs.
- Reuse an existing implementation when its business meaning, validation, tenant
  and permission boundaries, transaction behavior, exceptions and side effects fit.
  A similar signature is not enough. Do not bypass a boundary to force reuse.
- When affected paths express the same business rule and must change together,
  keep that rule in one appropriate place. Do not copy a method and adjust names
  or constants instead of using the shared rule. Verify all affected callers.
- Choose the smallest useful boundary: a private helper for repetition within a
  class, or an existing business owner/shared component when genuinely needed
  across classes. Preserve behavior and public contracts while extracting.
- Similar-looking code may represent different rules that evolve independently.
  Keep those implementations separate; do not merge them by adding boolean
  switches, callbacks or type checks solely to eliminate visual duplication.
- Build abstractions for actual uses. Do not add a generic executor, base class,
  strategy hierarchy or new dependency for hypothetical reuse. Limit cleanup to
  the authorized change; avoid unrelated repository-wide deduplication.

In an existing checkout component, delegate to the already established delivery
fee policy instead of copying its calculation. The component below already owns
`deliveryFees`; its normal production construction is omitted:

```java
/**
 * Returns the confirmed fee using the same policy as the preview.
 *
 * @param subtotalCents non-negative order subtotal in minor currency units
 * @return the fee produced by the existing delivery policy
 * @throws IllegalArgumentException if the subtotal is negative
 */
public long confirmedFee(long subtotalCents) {
    return deliveryFees.feeFor(subtotalCents);
}
```

Do not create a new policy type just to reproduce this example. A smaller diff,
fewer lines, a method name or passing output tests alone does not establish that
the appropriate implementation was reused or that one rule has one owner.

## Avoid nested types unless they are necessary

Prefer top-level types in the existing business package for business DTOs,
results, policies and Spring-managed components, with only the visibility they
need. This applies to inner classes, static nested classes, and nested records,
enums or interfaces; adding `static` does not resolve responsibility or navigation.
Do not hide a business type inside a service or Bean merely to avoid another file.

Retain a nested type only for a concrete need, such as an implementation that
requires close enclosing-instance encapsulation, or a necessary framework/test
structure. Being private, short or used by one caller does not by itself make
nesting necessary. Keep any retained nested implementation small and local.
Use existing framework conventions where required; this is a maintainability
preference, not a claim that Spring cannot support nested component types.

For example, a business quote result normally has its own top-level source file:

```java
/**
 * Delivery quote exposed by the business operation.
 *
 * @param feeCents delivery fee in minor currency units
 * @param currency currency code used by the quote
 */
record DeliveryQuote(long feeCents, String currency) {
}
```

Follow the project's actual Java version rather than introducing record syntax
where unavailable. Moving an existing nested type can change its binary name,
visibility, serialization or dependency wiring. Preserve those contracts and
stay within the task; this rule does not authorize a historical type migration.
