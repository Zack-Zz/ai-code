# Routing evidence workspace

These anonymous module snapshots are inspection inputs for routing cases. They
are not a complete application, resolved dependency graph, or framework runtime
test. Do not download dependencies to turn them into one. Use the module POMs,
full imports, mapped XML and call sites as evidence, and record any provider or
runtime facts that remain unverified.

- The parent POM manages a JPA API version; `plain` does not use that API.
- `jpa` declares EclipseLink and Hibernate Validator. Validator is not an ORM
  provider. Its entity includes non-delete cascade behavior and a real framework
  constructor. Changing only its mapping annotations still changes persistence
  behavior; changing only Javadoc does not.
- `mybatis` has a Java Mapper bound to XML, including tenant-scoped parameters.
- `mapping` uses MapStruct's Mapper annotation, not MyBatis's annotation.
- `test-only` places JPA solely in test scope; its production code is plain Java.
- `unknown-store` deliberately does not reveal its client's storage mechanism.
- `frontend` is a separate TypeScript/React package, outside the Java rule scope.

For a mixed-path case, use the described change across the existing JPA and
MyBatis modules. A candidate's output and reading trace must be evaluated; the
presence of these files alone does not establish any successful model routing.
