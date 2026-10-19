# CodeStack

English | [简体中文](README.zh-CN.md)

CodeStack guides a coding assistant through explicit Java writing conventions
and targeted persistence pitfalls. Its plugin ID is `ai-code-stack-standards`.
This is a development preview; it has not been published to the stable marketplace.

## Use

Once installed and enabled through your host's native plugin mechanism, describe
your ordinary Java implementation or review task:

- “Add this field and its accessors to the existing Java class.”
- “Add tests for this service using its production construction path.”
- “Fix the order-list query that loads each customer separately.”
- “Review this MyBatis Mapper and its XML parameter bindings.”

The `code-standards` skill is intended to be selected automatically for relevant
work. You can explicitly invoke it if needed. Automatic discovery and task
outcomes must be verified in the actual host; installation alone does not prove
that every task will use the skill. See the repository's
[development guide](../../CONTRIBUTING.md) for local packages and trials.
The repository's [installation guide](../../docs/installation.md) lists release
records and marketplace sources. This preview is not currently listed there for
stable installation. CodeStack can be used independently of CodeVow and Agent
Delegation; it introduces no dependency on either plugin.

## What it applies

- Comment language: user requirement, then project/module language, then the
  configured host/system language. English rule text does not force English comments.
- Multiline Javadoc for handwritten fields, methods, constructors and parameters;
  concise inline comments only for core logic.
- Test-specific construction stays inside the test class, without production-only
  test constructors or disguised entry points.
- Reuse suitable existing implementations and give one business rule a suitable
  owner. Preserve independent implementations when their semantics differ.
- Prefer top-level business types and Spring components; retain nested types only
  for a concrete need, without migrating unrelated historical code.
- SQL access stays bounded and avoids per-item queries, including hidden lazy,
  parallel and cache-miss paths. Query-cost claims require appropriate evidence.
- JPA and MyBatis references are selected only for the affected mechanisms.
  A mixed project can use both; a MapStruct mapper or an unrelated XML file does
  not imply MyBatis.

One English skill loads only relevant English references. CodeStack requires no
project configuration, injected AGENTS instruction, runtime, hook or separate
agent. Existing workflows, tools and dependencies remain the task's context.
Reviews report findings within their authorized scope. Java formatting, generic
tutorials and non-Java stack rules are outside this preview.

## Resources and license

- [Skill entry](skills/code-standards/SKILL.md)
- [Java](skills/code-standards/references/java.md), [data access](skills/code-standards/references/data-access.md), [JPA](skills/code-standards/references/jpa.md), [MyBatis](skills/code-standards/references/mybatis.md)
- [Evaluation cases](evals/cases.md): source-only fixtures and acceptance criteria

The shared build packages only the allowlisted skill, references and license.
Human-facing source guides and evaluation inputs are not execution resources.
Release workflow registration and public publication are separate from this preview.

[MIT](LICENSE). Maintained by Zack-Zz.
