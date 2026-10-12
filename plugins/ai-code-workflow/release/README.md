# CodeVow — AI Coding Workflow

English | [简体中文](README_CN.md)

CodeVow helps your AI coding assistant turn a request into a planned, tested
and reviewed change. It brings plan-first collaboration, TDD, evidence-driven
debugging and final-state verification to Claude Code, Codex and ZCode.
The plugin ID is `ai-code-workflow`.

## Install and start

Follow the [installation guide](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.md) to register the marketplace,
choose CodeVow, and install and enable it. Available plugins are listed in the
marketplace. The guide also covers Release downloads, updates and uninstalling.

Start a new session and describe your goal, scope and acceptance conditions:

> Add a bulk discount tier. Keep existing pricing behavior unchanged and
> test the boundaries. Show me the plan before implementation.

You can also ask for a focused investigation or review:

> Diagnose the intermittent timeout from logs and code before changing anything.
>
> Review this diff for authorization and data consistency risks.

## Connect a project entry

Skill descriptions help the host select skills; they do not guarantee that
`workflow` is read before every request. For a persistent entry for coding-related
tasks, use a project-instruction entry your host actually provides and whose
loading you have checked. Add a short instruction yourself:

```text
For coding-related tasks, first load the installed CodeVow workflow skill to
classify the request and check actual user conversation authorization.
Without development authorization, questions, investigations and independent
reviews default to read-only; confirmed defects do not authorize tests,
diagnostic files or fixes. Follow-up questions during authorized development
do not revoke that authorization; explicit stop requests and limits still apply.
In collaborative mode, show proposed changes and wait for applicable
confirmation; reuse confirmation covering the scope and keep moving within it.
Continuous mode grants no new authorization. Load other skill bodies only for
the current stage and reuse valid context. If workflow cannot load, report it
and remain read-only.
```

Keep this entry separate from the skill bodies: workflow rules remain in the
skills. Use a project-instruction entry your host actually provides, after
checking how it loads in your session. This snippet is for your active opt-in;
CodeVow does not silently edit existing `AGENTS.md`, `CLAUDE.md` or host settings.
This does not assume a fixed installation-cache path or that a bundled
`AGENTS.md` activates automatically. The exact instruction location and
loading behavior need verification in your actual host session.

You can explicitly ask the host to load the installed CodeVow `workflow` skill
and check that it can read it, keeping the check read-only. If loading fails,
the assistant should tell you and remain read-only. Successful loading proves
access in that session, not automatic routing or compliance for every request.
See the [usage guide](https://github.com/Zack-Zz/ai-code/blob/main/plugins/ai-code-workflow/docs/usage.md#connect-the-project-entry).

## How it works

| Skill | What it helps with |
|---|---|
| `workflow` | Clarify the request, agree on a proportionate plan and organize the work |
| `tdd` | Start behavior changes with a meaningful failing test, then implement and refactor |
| `debugging` | Use hypotheses and small experiments to identify the cause |
| `review` | Review affected risks, verify findings and attempt independent review when required |
| `verification` | Check the final code state and report actual verification |
| `review-results` | Present conclusions with clear impact and clickable evidence |

Without development authorization, questions, investigations and independent
reviews default to read-only; confirming a defect does not authorize tests,
diagnostic files or fixes. Follow-up questions during authorized development
do not revoke that authorization; explicit stop requests and scope limits still
apply. The default `collaborative` mode shows proposed changes and waits for applicable
confirmation before implementation, reusing confirmation that covers the
scope. `continuous` mode keeps work moving within the scope you have explicitly
authorized and grants no new authorization.

Both modes preserve existing edits. Commit, push, tag, merge, PR creation,
installation and external publication each need your explicit authorization.
A mode switch or task record does not grant it.

## Project configuration

Create `.ai-workflow/policy.json` in your project to set preferences:

```json
{
  "schema_version": 1,
  "mode": "collaborative",
  "response_language": "en",
  "verification_notes": ["Run the relevant tests before delivery"]
}
```

Defaults come from [collaborative](policies/collaborative.json) or
[continuous](policies/continuous.json). Project settings override the defaults;
explicit conversation options take precedence. The
[usage guide](https://github.com/Zack-Zz/ai-code/blob/main/plugins/ai-code-workflow/docs/usage.md) covers all settings, policy inspection, optional
task records and project file staging.

The plugin uses your host, account and selected model. Markdown skills need
no additional Node.js or Python. Optional tools need Python 3.11+; file staging
needs a platform supporting POSIX file operations. The Python tool makes no
network or model calls and performs no Git operations.

## More help and license

- [Installation, updates and uninstalling](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.md)
- [Usage and advanced tools](https://github.com/Zack-Zz/ai-code/blob/main/plugins/ai-code-workflow/docs/usage.md)
- [Workflow rules](skills/workflow/SKILL.md) and [policy schema](schemas/policy.schema.json)

MIT — see [LICENSE](LICENSE), [NOTICE](NOTICE) and the preserved
[backend-engineering-lite license](LICENSES/backend-engineering-lite.txt).
CodeVow's workflows evolved from backend-engineering-lite in this repository;
the repository's early history derives from Affaan Mustafa's ai-code.
