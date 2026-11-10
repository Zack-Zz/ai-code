---
name: code-standards
description: Use when implementing or reviewing helpers or shared logic in any language, or when implementing, changing, or reviewing Java code, SQL/JPA/MyBatis persistence, or user-visible frontend copy in a product with existing or explicitly requested multilingual support. Apply only the relevant conventions.
origin: codestack
---

# CodeStack

Use the task's existing workflow and authorization. A review request permits
inspection and findings. Repairs require an applicable grant.

## Reuse or extract shared implementations

1. Before adding a helper in any language, inspect similar call sites in the
   current module, then related modules. Trace imports or references to the actual
   implementation. Reuse it directly if it is available and its inputs, results,
   validation, errors, side effects and boundaries fit.
2. If no suitable implementation exists, extract behavior needed by multiple
   callers to the narrowest shared owner. Put general operations in a shared
   utility and business rules with their domain owner. Preserve contracts and
   verify affected callers.
3. Keep class- or module-specific orchestration local and call shared operations
   from it. Keep independently evolving rules separate. Extract for actual
   callers within the task's scope.

## Select rules before the affected work

Identify the affected files, modules and call paths before editing or reviewing.
Read only the references that apply:

| Reference | Read when | Apply to |
| --- | --- | --- |
| [Java](references/java.md) and its [construction and type placement companion](references/java-design.md) | Writing, changing or reviewing handwritten Java declarations, implementations or tests | Type imports and references, comment language, complete multiline Javadoc, inline comments, test construction and necessary-only nested types |
| [Data access](references/data-access.md) | Implementing, changing or reviewing confirmed relational/SQL access or its cost | Hidden per-item queries, bounded loading, result contracts and actual database work |
| [JPA](references/jpa.md) | The change affects JPA mapping, entity construction, lifecycle, queries or persistence calls | Implicit loading/writes, delete propagation, pagination and provider-specific batching |
| [MyBatis](references/mybatis.md) | The change affects actual MyBatis Mapper, XML, SqlSession or related calls | Binding, dynamic SQL, nested selects and actual pagination/batch execution |
| [Frontend](references/frontend.md) | Implementing, changing or reviewing fixed user-visible copy in a frontend product with existing or explicitly requested multilingual support | Centrally maintained language resources, referenced by keys across pages, components and actions |

Combine references for one operation that actually uses both JPA and MyBatis.
Keep shared data-access requirements in their shared reference; framework rules
add relevant mechanisms, not alternative versions of the shared requirements.

For a documentation-comment-only Java edit, read Java rules and just enough source
to understand the comment. An entity's framework affiliation alone does not
justify SQL investigation, mapping changes or additional integration tests.
Changes to persistence annotations can affect mapping, loading or lifecycle;
select the relevant persistence references even if no method body changes.
For confirmed MyBatis mapper XML, select data-access and MyBatis rules, not
Java Javadoc. JPA mapping or persistence XML uses the relevant JPA rules;
select shared data-access rules when SQL behavior or cost is affected. Other
XML does not acquire persistence rules from its file extension. Apply Java
rules to related handwritten Java declarations only when those declarations
are in the task scope. Pure conceptual questions, unrelated prose edits and
work unrelated to these supported mechanisms need no default loading of their
references. For frontend work, select the shared frontend reference only when
the task affects user-visible copy and the product has existing or explicitly
requested multilingual support. A single-language UI label, backend-only
TypeScript change or CSS-only edit does not select that reference. Frontend work
does not select Java or persistence references without a relevant affected path.

## Establish the actual stack

- Prefer complete imports, inherited types, invoked APIs, injected components,
  bound XML statements and the current module's effective dependencies.
- Dependency management/BOM entries, another module's dependencies, inactive
  configuration and migration remnants do not establish current use.
- A test dependency does not establish the production stack. When the task
  changes a test that actually uses that framework, consider its real use.
- `org.mapstruct.Mapper` is a mapping annotation, not a MyBatis declaration.
  A class called Mapper or Repository is not enough evidence of persistence.
  Follow hand-written mapping calls if they hide database access.
- JPA does not establish Hibernate ORM. Confirm the provider and version before
  using Hibernate-specific conclusions; Hibernate Validator is not Hibernate ORM.
  For direct Hibernate ORM usage, apply only the relevant ORM rules, without
  assuming JPA APIs are present.
- Confirmed JDBC or another SQL-based implementation can use shared data-access
  rules without adopting JPA or MyBatis. Investigate unknown storage; do not
  apply SQL/IN/JOIN assumptions to non-relational storage or claim full coverage.
- A user-specified stack for a new module is a valid development target even
  before its dependencies exist. It does not authorize unrelated dependency
  installation or silently converting an existing module to another stack.
- Establish multilingual frontend scope from the current application's locale
  switching, message lookups and resource configuration, or an explicit product
  requirement. An internationalization dependency, a React/Vue file or another
  application's languages alone is not enough. Follow the current application's
  resource boundary in a mixed repository; do not introduce multilingual support
  into an unrelated single-language product.

If the user's description and source disagree, investigate first. Ask only when
the unresolved difference affects the authorized work. Never require a new
project configuration file to select these rules.

## Apply and reuse

Reuse the current scope, selection evidence and already-read references while
they remain applicable. Add a reference when a new affected call path requires
it; do not rescan the repository before every edit or load every reference by default.
Keep this decision in conversation context, not a project cache or task file.

Follow explicit user requirements and applicable project contracts. Existing
code without comments does not waive an explicit Javadoc requirement; an old
per-item query is not permission to add another. Do not turn suggestions or
uncertain framework assumptions into confirmed violations.

Use the project's existing stack, dependencies and tools. Do not add hooks,
agents, global settings, project rules or runtime classifiers. Do not change
unrelated files, reformat code, invent author/version metadata, or migrate the
architecture to match an example. Generated/vendor code follows its maintenance
source; do not hand-copy generated members to add comments.

During normal implementation, apply the rules without printing a checklist.
When reporting a problem, give the applicable requirement, source location,
concrete impact and suggested correction. Distinguish expected behavior from
measured results. Neither reading this skill nor passing package checks proves
native automatic invocation or correct task outcomes.
