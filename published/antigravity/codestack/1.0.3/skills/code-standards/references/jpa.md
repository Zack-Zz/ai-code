# JPA and provider-specific pitfalls

Read for affected JPA mapping, entity construction, lifecycle, queries or
persistence calls. Apply [shared data-access rules](data-access.md) to affected
SQL behavior and [Java rules](java.md) to relevant handwritten Java declarations.
Comment-only entity edits do not require investigating the persistence stack.

Confirm the actual provider and version before provider-specific conclusions.
Hibernate Validator is not Hibernate ORM. For direct Hibernate APIs, use only
the applicable ORM mechanisms rather than assuming JPA API usage.

## Check implicit work

- Follow association traversal, getters, DTO conversion and serialization to
  actual SQL. Changing to LAZY or adding an EntityGraph does not prove N+1 is
  gone. Do not change every association to EAGER.
- With collection fetch joins and pagination, verify actual SQL, where paging
  occurs, count queries, result cardinality and join multiplication. Returning
  a Page does not establish bounded database-side pagination.
- Do not mutate managed entities or associations just to format a response.
  Dirty checking can persist those changes; "no save call" does not establish
  that no write occurs. Use the project's existing read/result boundary.

## Check deletion and batch claims

When changing cascade options, verify the specific propagated operation.
For REMOVE, ALL that includes REMOVE, and orphanRemoval, additionally confirm
the intended child lifecycle and deletion scope. Do not copy deletion settings
merely to simplify mapping or treat non-delete PERSIST/MERGE propagation as an
ownership declaration. Preserve existing behavior that the business actually requires.

A saveAll-style API or batch_size setting does not prove batching. Distinguish
SQL statements, JDBC batching and database round trips. For example, Hibernate
ORM 6.6 disables JDBC insert batching for IDENTITY identifiers; check the actual
provider/version before applying that conclusion elsewhere. Do not change ID
generation or global ORM settings merely to make an example look optimized.

## Preserve genuine framework construction

A framework-required constructor serves production. It is allowed; an additional
test-only constructor or validation bypass is not. Choose the actual project's
annotation package and JPA version. This fragment only illustrates that boundary:

```java
/**
 * Persistent order entity.
 */
@Entity
public class OrderEntity {
    /**
     * Unique order identifier.
     */
    @Id
    private Long id;

    /**
     * Allows the JPA provider to instantiate this entity.
     */
    protected OrderEntity() {
    }
}
```

Do not force JPA on other modules, switch providers, disable OSIV by default or
copy a complete entity template into unrelated code.

Mechanism references: [Jakarta Persistence](https://jakarta.ee/specifications/persistence/3.2/jakarta-persistence-spec-3.2.html),
[Hibernate ORM 6.6 batching](https://docs.hibernate.org/orm/6.6/userguide/html_single/#batch),
[Hibernate fetch joins](https://docs.jboss.org/hibernate/orm/7.0/querylanguage/html_single/Hibernate_Query_Language.html).
These sources describe their own versions, not the target project's baseline.
