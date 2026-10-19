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

Keep this entry separate from the skill bodies. Actively add or merge it
into your host's project instructions, preserving existing content. CodeVow
does not write configuration automatically. The snippet assumes neither a
fixed installation-cache path nor automatic activation of a bundled `AGENTS.md`.

ZCode natively reads global `~/.zcode/AGENTS.md` and `AGENTS.md` at the current
Workspace root. For this project, add or merge the snippet into the Workspace-root
file; ZCode does not scan subdirectories or expand `@include`. `CLAUDE.md` is
only offered for a one-time onboarding migration, not read as a native entry
afterward. See [ZCode's AGENTS.md guide](https://zcode.z.ai/en/docs/agents).

CodeVow's `collaborative` / `continuous` are workflow instructions; they do not
switch ZCode's native execution mode or intercept editing tools. ZCode's Plan
Mode can present a plan for confirmation before editing. These instructions
do not establish real-host acceptance; verify loading and adherence in your session.

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
apply.

## Choose a collaboration mode

Choose whether you want to confirm the proposed plan before the assistant starts
editing:

| Mode | How work starts | Choose it when |
|---|---|---|
| `collaborative` — collaborative mode (default) | The assistant investigates, explains the proposed change and waits for you to confirm the plan before editing. | You want to review the approach before implementation. |
| `continuous` — continuous mode | After you ask it to implement a task, the assistant explains a short plan and proceeds within the scope you authorized. | The goal and scope are clear, and you want the assistant to carry the task through. |

Mixed wording needs the same authorization check. For example: "Add an entry
in DevOps to initialize product-line application clients. Could you look into
how to handle this?" With no prior authorization, the assistant first
investigates read-only and proposes an approach; the word "add" alone does
not authorize development. In default `collaborative` mode, even an explicit
implementation request needs a presented plan and your confirmation before
any project write, including tests or diagnostic files. Ordinary follow-up
questions within an already confirmed scope do not require confirmation again.

Once implementation starts, both modes continue through coding, testing and
review without asking you to approve every ordinary step. Previously confirmed
plans are reused. If the scope or a key decision changes materially, the assistant
asks you to confirm the affected part.

Both modes keep the same testing, review and verification requirements and
preserve your existing edits. Requests only for explanation or investigation
stay read-only; follow-up questions during an authorized task do not cancel
work you have already permitted.
Commit, push, tag, merge, PR creation, installation and external publication
still need your explicit instructions; a mode switch or task record does not
grant permission.

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

The default mode is `collaborative`. Set `mode` to `continuous` to use the
continuous mode described above. Project settings override the packaged defaults;
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
