# CodeVow — AI Coding Workflow

English | [简体中文](README.zh-CN.md)

CodeVow `codevow` 1.0.6 is published. The old plugin ID is retired.
The [published record](https://github.com/Zack-Zz/ai-code/blob/main/published/index.json)
is authoritative; released snapshots remain immutable.

CodeVow helps your AI coding assistant turn a request into a planned, tested
and reviewed change. It brings plan-first collaboration, TDD, evidence-driven
debugging and final-state verification to Claude Code, Codex, ZCode and DeepSeek Harness.
The plugin ID is `codevow`.

## Install and start

Follow the [installation guide](../../docs/installation.md) to register the marketplace,
choose CodeVow, and install and enable it. Available plugins are listed in the
marketplace. The guide also covers Release downloads, updates and uninstalling.

Choose the guide for your host: [Codex desktop and CLI](../../docs/installation.md#codex),
[Claude Code desktop and CLI](../../docs/installation.md#claude-code),
[ZCode desktop and macOS bundled CLI](../../docs/installation.md#zcode), or
[DeepSeek Harness desktop and standalone npm CLI](../../docs/installation.md#deepseek-harness).

Start a new session and describe your goal, scope and acceptance conditions:

> Add a bulk discount tier. Keep existing pricing behavior unchanged and
> test the boundaries. Show me the plan before implementation.

You can also ask for a focused investigation or review:

> Diagnose the intermittent timeout from logs and code before changing anything.
>
> Review this diff for authorization and data consistency risks.

Skill descriptions help the host choose skills; installation alone does not
guarantee that `workflow` runs first. The [project entry guide](docs/usage.md#connect-the-project-entry)
provides a short, optional instruction for coding-related tasks that you can
connect through your host's verified project-instruction entry. It also explains
direct skill invocation, authorization checks and actual host verification.

## How it works

| Skill | What it helps with |
|---|---|
| `workflow` | Clarify the request, agree on a proportionate plan and organize the work |
| `tdd` | Start behavior changes with a meaningful failing test, then implement and refactor |
| `debugging` | Use hypotheses and small experiments to identify the cause |
| `review` | Review affected risks, verify findings and attempt independent review when required |
| `verification` | Check the final code state and report actual verification |
| `review-results` | Present conclusions with clear impact and clickable evidence |

## Choose a collaboration mode

Choose whether you want to confirm the proposed plan before the assistant starts
editing:

| Mode | How work starts | Choose it when |
|---|---|---|
| `collaborative` — collaborative mode (default) | The assistant investigates, explains the proposed change and waits for you to confirm the plan before editing. | You want to review the approach before implementation. |
| `continuous` — continuous mode | After you ask it to implement a task, the assistant explains a short plan and proceeds within the scope you authorized. | The goal and scope are clear, and you want the assistant to carry the task through. |

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
[usage guide](docs/usage.md) covers all settings, policy inspection, optional
task records and project file staging.

The plugin uses your host, account and selected model. Markdown skills need
no additional Node.js or Python. Optional tools need Python 3.11+; file staging
needs a platform supporting POSIX file operations. The Python tool makes no
network or model calls and performs no Git operations.

## More help and license

- [Installation, updates and uninstalling](../../docs/installation.md)
- [Usage and advanced tools](docs/usage.md)
- [Workflow rules](skills/workflow/SKILL.md) and [policy schema](schemas/policy.schema.json)

MIT — see [LICENSE](LICENSE), [NOTICE](NOTICE) and the preserved
[backend-engineering-lite license](LICENSES/backend-engineering-lite.txt).
CodeVow's workflows evolved from backend-engineering-lite in this repository;
the repository's early history derives from Affaan Mustafa's ai-code.

## DeepSeek Harness

The bundle and [custom marketplace index](https://raw.githubusercontent.com/Zack-Zz/ai-code/main/published/dsh/index.json)
are published. The desktop app bundles Node.js and pnpm; a separate npm CLI
installation is unnecessary. Desktop and standalone npm CLI steps are in the
[Harness installation guide](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.md#deepseek-harness).
The released bundle pins `engines.dsh` and its DSH peer dependencies to
`0.2.1-rc.2`; desktop `0.2.1-rc.3` is outside that declaration. Real desktop
acceptance, native loading, implicit selection, long sessions and lifecycle
acceptance remain unverified. Build and package checks do not establish host acceptance.
Invoke the skill with `/workflow`. Independent
official filesystem providers expose each plugin's bundled resources.

Independent review uses `workflow_reviewer` with the `codevow-reviewer` preset
and only read/grep/glob. The profile must supply agentPresets, Agent/tool/prompt
services and the subagents spawn backend. Missing services produce native Loader
activation diagnostics; that profile is unsupported. Python helpers still require
Python 3.11+; without Python, follow the skill's manual policy resolution and
report unavailable checks. The tool allowlist is separate from filesystem isolation;
read roots continue to use the host's permissions.

See the [identity migration guide](https://github.com/Zack-Zz/ai-code/blob/main/docs/migrations/2026-10-27-plugin-identities.md) for uninstall and reinstall steps.
