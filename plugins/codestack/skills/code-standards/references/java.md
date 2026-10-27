# Java writing requirements

Apply to handwritten Java code and tests in the current change or review scope.
These are CodeStack's explicit conventions, not claims that Java requires every
declaration to be documented. Do not expand into unrelated files or a general
Java style tutorial. Code indentation, line wrapping, line width, blank lines
and import ordering are outside these conventions.

## Choose the comment language

Use, in order: the user's explicit requirement; the current project/module's
established comment and documentation language; the configured host/system
language (Chinese or English) when the project has none. English Java keywords,
this English reference, and the conversation language do not override a known
project language. Keep API/type names unchanged and do not translate unrelated
comments. Use the chosen language consistently within a declaration's docs.

## Document every handwritten field and method

- Write multiline Javadoc for every field: private, static, constants and enum
  constants included. Document every method, including private methods,
  interface/override methods, getters/setters and test methods. Document constructors.
- Put the opening marker, content and closing marker on separate lines. Never
  use a one-line documentation comment, even for a one-sentence description.
- Explain each method/constructor parameter using `@param`; explain generic
  parameters with `@param <T>`. State meaning, units, bounds and nullability when
  relevant instead of repeating the parameter name.
- Add `@return` for non-void methods, including meaningful empty/null semantics.
  Do not add it to constructors or void methods. Document exceptions the caller
  must handle with `@throws` and the triggering condition.
- Document record components with type-level `@param`. Do not reimplement
  generated members solely to attach documentation.
- State real behavior. A comment saying "validated", "batched" or "idempotent"
  does not implement or prove that behavior. Locate the actual validation or
  execution path before making that claim. Keep docs synchronized with changes.

```java
/**
 * Order amount in minor currency units.
 */
final class OrderAmount {
    /**
     * Non-negative amount in minor currency units.
     */
    private final long cents;

    /**
     * Creates an order amount.
     *
     * @param cents non-negative amount in minor currency units
     * @throws IllegalArgumentException if the amount is negative
     */
    OrderAmount(long cents) {
        if (cents < 0) {
            throw new IllegalArgumentException("Amount must not be negative");
        }
        this.cents = cents;
    }

    /**
     * Returns the amount in minor currency units.
     *
     * @return the non-negative amount
     */
    long getCents() {
        return cents;
    }
}
```

The English example illustrates syntax; choose the target comment language by
the precedence above. Adapt syntax/API usage to the project's actual Java version.

## Comment only the core logic inside methods

Use short, direct line comments for important business decisions, calculation
reasons, concurrency behavior or easily misunderstood logic. Do not narrate
assignments, calls and returns, or use Javadoc for local variables. Remove stale
explanations and commented-out obsolete code rather than copying them forward.

## Construction, reuse and type placement

Read [Java construction, reuse and type placement](java-design.md) in full for
Java implementation and test changes, and before forming a related review finding.
It continues these rules: keep test construction inside the test class; reuse
existing implementations and consolidate the same rule; avoid nested types unless
they are necessary. The companion is part of the Java contract, not optional advice.
For a documentation-comment-only edit, read enough affected source to understand
the comment; do not expand into unrelated construction or architecture changes.
