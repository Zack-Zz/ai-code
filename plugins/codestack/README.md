# CodeStack

English | [简体中文](README.zh-CN.md)

CodeStack `codestack` 1.0.0 is published. The old plugin ID is retired.
The [published record](https://github.com/Zack-Zz/ai-code/blob/main/published/index.json)
is authoritative; released snapshots remain immutable.

<img src="assets/codestack.png" alt="CodeStack icon" width="96" />

CodeStack supplies a coding assistant with selected project conventions across
supported languages and stacks. It currently covers Java writing, targeted
SQL/JPA/MyBatis pitfalls, and shared multilingual frontend copy organization.
Its plugin ID is `codestack`.
Stable releases are distributed through the shared `ai-code` marketplace. Check the
[current release record](https://github.com/Zack-Zz/ai-code/blob/main/published/index.json) for availability.

## Install

Choose the guide for your host: [Codex desktop and CLI](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.md#codex),
[Claude Code desktop and CLI](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.md#claude-code),
[ZCode desktop and macOS bundled CLI](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.md#zcode), or
[DeepSeek Harness desktop and standalone npm CLI](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.md#deepseek-harness).

Select `codestack` from the shared `ai-code` marketplace.

## Use

Once installed and enabled through your host's native plugin mechanism, describe
your ordinary implementation or review task:

- “Add this field and its accessors to the existing Java class.”
- “Add tests for this service using its production construction path.”
- “Fix the order-list query that loads each customer separately.”
- “Review this MyBatis Mapper and its XML parameter bindings.”
- “Add a confirmation dialog and feedback to this multilingual React page.”
- “Review the validation messages in this multilingual Vue form.”

The `code-standards` skill is intended to be selected automatically for relevant
work. You can explicitly invoke it if needed. Automatic discovery and task
outcomes must be verified in the actual host; installation alone does not prove
that every task will use the skill. CodeStack is installed independently and can
be used independently of CodeVow and Agent Delegation; it introduces no dependency
on either plugin.

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
- In a frontend product with existing or explicitly requested multilingual
  support, keep affected fixed user-visible copy in a dedicated, centrally
  maintained language-resource area. Pages, components and actions use resource
  keys. This includes labels, placeholders, accessible text, dialogs, validation
  and feedback; dynamic business data remains data. Resources may be split by
  language or domain using the existing localization mechanism.

The frontend convention is shared across JavaScript/TypeScript, React, Vue and
other frontend stacks. Single-language products, backend-only TypeScript and
copy-unrelated edits do not acquire this requirement. Existing Java conventions
are not generalized to frontend code. There are no separate TypeScript, React or
Vue rule references without additional approved rules.

One English skill loads only relevant English references. CodeStack requires no
project configuration, injected AGENTS instruction, runtime, hook or separate
agent. Existing workflows, tools and dependencies remain the task's context.
Reviews report findings within their authorized scope. Formatting, generic
tutorials and rules beyond the explicitly supported areas are outside this plugin's scope.
These are explicit project conventions; behavioral improvement and native host
selection require measured evidence rather than the existence of a rule file.

## Resources and license

- [Skill entry](skills/code-standards/SKILL.md)
- [Java](skills/code-standards/references/java.md), [data access](skills/code-standards/references/data-access.md), [JPA](skills/code-standards/references/jpa.md), [MyBatis](skills/code-standards/references/mybatis.md), [frontend](skills/code-standards/references/frontend.md)
- [Evaluation cases](evals/cases.md): source-only fixtures and acceptance criteria

The shared build packages only the allowlisted skill, references, icon and license.
Portable English and Chinese READMEs accompany the execution resources. Evaluation
inputs stay outside installation packages. Publishing and real host acceptance
are separate results.

[MIT](LICENSE). Maintained by Zack-Zz.

## DeepSeek Harness

The bundle and [custom marketplace index](https://raw.githubusercontent.com/Zack-Zz/ai-code/main/published/dsh/index.json)
are published. The desktop app bundles Node.js and pnpm; a separate npm CLI
installation is unnecessary. Desktop and standalone npm CLI steps are in the
[Harness installation guide](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.md#deepseek-harness).
The released bundle pins `engines.dsh` and its DSH peer dependencies to
`0.2.1-rc.2`; desktop `0.2.1-rc.3` is outside that declaration. Real desktop
acceptance, native loading, implicit selection, long sessions and lifecycle
acceptance remain unverified. Build and package checks do not establish host acceptance.
Invoke the skill with `/code-standards`. Independent
official filesystem providers expose each plugin's bundled resources.

See the [identity migration guide](https://github.com/Zack-Zz/ai-code/blob/main/docs/migrations/2026-10-27-plugin-identities.md) for uninstall and reinstall steps.
