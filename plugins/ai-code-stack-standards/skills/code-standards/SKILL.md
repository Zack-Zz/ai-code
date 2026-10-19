---
name: code-standards
description: Use when implementing, changing, or reviewing Java code or JPA/MyBatis persistence mappings; apply CodeStack's comment, test-construction, and data-access rules to the affected code.
origin: ai-code-stack-standards
---

# CodeStack

Apply the explicit writing requirements and targeted mistake prevention below.
Use the current task's authorization and workflow. A review request permits
inspection and findings, not repairs. Do not introduce a second planning,
approval, testing or review process.

## Select rules before the affected work

Before writing relevant code, or forming a review finding, identify the current
files, module, kind of change and necessary call paths. Read only the references
that apply:

| Reference | Read when | Apply to |
| --- | --- | --- |
| [Java](references/java.md) | Writing, changing or reviewing handwritten Java declarations, implementations or tests | Comment language, complete multiline Javadoc, inline comments, test construction, existing-code reuse, appropriate extraction and necessary-only nested types |
| [Data access](references/data-access.md) | Implementing, changing or reviewing confirmed relational/SQL access or its cost | Hidden per-item queries, bounded loading, result contracts and actual database work |
| [JPA](references/jpa.md) | The change affects JPA mapping, entity construction, lifecycle, queries or persistence calls | Implicit loading/writes, delete propagation, pagination and provider-specific batching |
| [MyBatis](references/mybatis.md) | The change affects actual MyBatis Mapper, XML, SqlSession or related calls | Binding, dynamic SQL, nested selects and actual pagination/batch execution |

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
work unrelated to Java or these persistence mechanisms need no default loading
of these references.

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

If the user's description and source disagree, investigate first. Ask only when
the unresolved difference affects the authorized work. Never require a new
project configuration file to select these rules.

## Apply and reuse

Reuse the current scope, selection evidence and already-read references while
they remain applicable. Add a reference when a new affected call path requires
it; do not rescan the repository before every edit or load all four by default.
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
