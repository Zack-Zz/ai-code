# MyBatis binding and hidden-query pitfalls

Read for affected MyBatis Mapper, XML, SqlSession or related access paths.
Confirm actual imports and bindings; a MapStruct mapper is not MyBatis.
Use [shared data-access rules](data-access.md) for SQL budgets, scope, empty
inputs and result contracts, and [Java rules](java.md) for relevant handwritten
Java declarations. Do not put Java Javadoc into XML.

## Keep Java and SQL bindings consistent

When changing either side, inspect the corresponding namespace, statement id,
Param names, foreach collection/item and result mapping. Java compilation does
not validate all SQL bindings. Read the relevant counterpart without expanding
the change into unrelated files.

Use `#{}` for ordinary values. `${}` is textual substitution, not parameter
binding: never feed it untrusted input. Select unavoidable dynamic identifiers
from a trusted allowlist; do not fix a binding failure by switching to substitution.
Check null/empty dynamic branches and defaults: an omitted predicate must not
expand access beyond the requested or authorized scope.

In this fragment, the method belongs to `example.UserMapper`, Param comes from
MyBatis, and `UserRow` is an existing plain result type. The real caller has
already enforced a nonempty, bounded set and tenant permissions:

```java
/**
 * Loads display information for the specified users in a tenant.
 *
 * @param tenantId tenant identifier obtained from trusted authentication context
 * @param userIds validated nonempty identifiers within the query limit
 * @return matching display information, or an empty list when none match
 */
List<UserRow> selectByIds(
        @Param("tenantId") long tenantId,
        @Param("userIds") Set<Long> userIds);
```

```xml
<mapper namespace="example.UserMapper">
    <select id="selectByIds" resultType="example.UserRow">
        SELECT id, display_name AS displayName
        FROM users
        WHERE tenant_id = #{tenantId}
          AND id IN
        <foreach collection="userIds" item="userId" open="(" separator="," close=")">
            #{userId}
        </foreach>
    </select>
</mapper>
```

Do not treat the documented caller preconditions as newly implemented checks.
Confirm their actual location. Empty input must be handled before this IN query;
do not simply wrap the predicate in an if and allow an unrestricted query.

## Inspect generated and deferred SQL

association/collection nested selects, lazy loading and mapping-time fallback
queries count toward the operation's SQL budget. A single Mapper invocation
does not prove the absence of N+1. Follow downstream result access as needed.

For paging, batching or caches, inspect the actual configured extension and
execution mode. Paging plugins can add count SQL; BATCH does not mean one SQL
statement. Do not change a global executor or plugin configuration merely to
satisfy a local rule. Keep actual session, transaction and data-source ownership
intact rather than adding manual lifecycle calls from a copied example.

MyBatis-Plus-specific wrappers, interceptors and logical deletion are outside
this first version's dedicated rules. Apply confirmed basic MyBatis mechanisms
where appropriate without claiming complete extension coverage.

Mechanism reference: [MyBatis mapped statements and result maps](https://mybatis.org/mybatis-3/sqlmap-xml.html).
