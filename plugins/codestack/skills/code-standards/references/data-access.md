# Shared SQL data-access requirements

Read when implementing, changing or reviewing confirmed relational/SQL access
or its cost. These requirements are shared by JPA, MyBatis, JDBC and other
confirmed SQL implementations. Do not infer SQL storage from an unknown database
or apply IN/JOIN assumptions to non-relational storage. Explicit user requirements
still apply independently. Read the actual affected access path, not every database module.

## Load in batches, then assemble in memory

- Do not query the database per item in `for`, `while`, streams, recursion or
  conversion functions. Follow getters, helpers, lazy associations and
  serialization: hidden N+1 queries are still per-item queries.
- Moving those queries into executors, `CompletableFuture` or parallel streams
  does not batch them. Per-item cache-miss fallback also does not waive this rule.
- Reuse loaded data, collect and deduplicate required identifiers, execute a
  bounded batch query or suitable join/projection, then assemble in memory.
  A method named batch/findByIds must not simply move the query loop inside.
- Preserve ordering, required duplicates and missing-related-data behavior.
  Deduplicating query keys does not authorize deduplicating the response.
  Do not fetch each missing association as a fallback or disguise query failure
  as an empty successful result.

The project's existing `userQuery` below performs one bounded tenant-scoped
query and returns plain result objects. Imports/business types are omitted.
The real entry must already validate permissions, non-null elements and the
input-size limit; a comment alone is not evidence of that validation.

```java
/**
 * Loads the specified users within the current tenant.
 *
 * @param tenantId tenant identifier obtained from trusted authentication context
 * @param userIds non-null, deduplicated identifiers within the validated query limit
 * @return matching users, or an empty list when no users match
 */
public List<UserRow> listUsers(long tenantId, Set<Long> userIds) {
    if (userIds.isEmpty()) {
        return Collections.emptyList();
    }
    return userQuery.findByIds(tenantId, userIds);
}
```

Do not add a new abstraction just to match this example. Result getters and
serialization must not introduce further hidden queries.

## Bound batch inputs and results

- Set and validate limits using actual database constraints and business budgets,
  not a copied universal number. An unbounded IN list or full-table load is not
  an acceptable replacement for a query loop.
- For a required positive identifier filter such as findByIds, return an empty
  result for an empty set without executing that lookup. Do not emit an empty
  IN or silently remove a required inclusion predicate.
- An empty exclusion set means no exclusions when that is the operation's
  contract. An optional filter may use empty input to mean no filtering only
  when the project explicitly defines that behavior. Preserve those result
  contracts rather than forcing an empty response. Keep tenant/permission
  constraints and result limits in every branch; never treat an empty set as
  permission to drop a required access constraint.
- Keep applicable tenant, permission, time and status predicates. Select only
  required rows/columns; do not load everything to paginate or filter access in Java.
- Bound page size and make ordering deterministic, including equal sort values.
  Stable ordering alone does not promise a cross-page snapshot.
- For exports/scans that genuinely require multiple query batches, reuse the
  already-authorized scope, batch size, query budget, termination and consistency
  requirements, including applicable project contracts. A local change within
  those bounds does not require another approval. Clarify a missing decision
  only when it affects the authorized work; obtain agreement before expanding
  an authorized range or budget. Do not silently turn per-item lookups into
  an alleged batching exception or weaken the no-per-item-query requirement.

Illustrative single-page SQL for a database supporting LIMIT; question marks are
bound values, and the actual dialect/binding follows the existing implementation:

```sql
SELECT id, status, created_at
FROM orders
WHERE tenant_id = ? AND status = ? AND id > ?
ORDER BY id
LIMIT ?
```

The tenant must come from trusted context and the last parameter must be a
validated page size. This example does not establish an effective index or
measured query cost.

## Assess actual database work

Before changing access code, establish expected SQL executions, accessed data
and table impact across the operation. Include count queries, permission checks,
association loading, serialization and fallback queries. One repository call
may execute multiple SQL statements.

Inspect filters, sorting, joins, index access, scanned/returned rows, result width,
row multiplication, applicable locks and connection occupancy. A small response
or an index name is not evidence of low cost. Do not indiscriminately add indexes.

For an order list plus customer names, design one bounded order query, one
deduplicated customer query and in-memory assembly. Report "at most two queries"
only after accounting for hidden SQL. A Mapper-call-count assertion is not that
evidence. Distinguish an expected budget from actual SQL traces, plans and
measurements; do not claim an optimization was measured when only code was read.
