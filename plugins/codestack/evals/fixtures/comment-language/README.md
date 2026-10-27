# Rate limit component

This module uses English code comments and documentation. It has no database or
framework dependencies. Compile the source and check with Java 17 or later into
a temporary output directory. Do not place class files in this fixture.

`RateLimit` stores a nonnegative per-request unit limit. Requests equal to the
limit are allowed. The existing check only covers the current constructor and
accessor; an implementation task can extend it with the requested behavior.
