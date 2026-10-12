# Using CodeVow

English | [简体中文](usage.zh-CN.md)

After [installation](../../../docs/installation.md), start a new host session
and describe the goal, change scope and acceptance conditions. CodeVow
organizes planning, TDD, debugging, review and verification around that request.

## Connect the project entry

Skill descriptions help the host select CodeVow skills. Installation and those
descriptions do not guarantee that the host reads `workflow` before every
request. For a persistent entry for coding-related tasks, use a project-instruction
entry your host actually provides and whose loading you have checked. Add a
short routing instruction yourself, for example:

```text
For coding-related tasks in this project, first load the installed CodeVow
workflow skill to classify the request and check actual user conversation authorization.
Without development authorization, questions, investigations and independent
reviews default to read-only; confirmed defects do not authorize tests,
diagnostic files or fixes. Follow-up questions during authorized development
do not revoke that authorization; explicit stop requests and limits still apply.
In collaborative mode, show the proposed changes and wait for applicable
confirmation; reuse confirmation that already covers the scope.
Continue within confirmed scope; continuous mode grants no new authorization.
Keep this entry short. Load other skill bodies only for the current stage and
reuse valid context. If workflow cannot load, report it and remain read-only.
```

Keep the persistent entry separate from the skill bodies. Workflow rules are
maintained in the [skills](../skills/workflow/SKILL.md); this snippet routes to
them instead of copying the full workflow into project instructions. Read only
the skill and referenced material needed at the current stage, and reuse valid
context rather than loading all six skills for every request.

Use a project-instruction entry actually provided by your host, after checking
how it loads in your session. This snippet is for your active opt-in. CodeVow
does not silently edit an existing `AGENTS.md`, `CLAUDE.md` or host setting.
The snippet assumes neither a fixed installation-cache path nor automatic activation of a bundled
`AGENTS.md`. The exact instruction location and its loading behavior need
verification in your actual host session.

To check entry loading, explicitly ask: "Load the installed CodeVow workflow
skill and tell me whether you can read it; keep this check read-only." Successful
loading confirms access in that session, not automatic routing or compliance
for every future request. If loading fails, the assistant should tell you and
remain read-only rather than claim CodeVow is active.

## Daily workflow

- Without development authorization, questions, investigations and independent
  reviews default to read-only. Finding or confirming a defect does not authorize
  writing tests, diagnostic files or repairs. A follow-up question during
  authorized development does not revoke that authorization; explicit stop
  requests and scope limits still apply.
- For development, it explains the proposed changes with a proportionate plan
  and waits for applicable scope confirmation under `collaborative`.
- Behavior changes start with a meaningful failing test, followed by the
  implementation and refactoring under the passing baseline.
- Debugging uses hypotheses and small experiments to locate the cause.
- Review focuses on affected risks; an independent review is attempted for
  critical risk or when the configured review level is `all`.
- Delivery reports the final code state, actual checks, findings and remaining
  work. Changed code needs fresh verification.

The default `collaborative` mode implements after applicable confirmation of
the proposed changes; existing confirmation covering that scope is reused.
`continuous` keeps moving within an already authorized scope and grants no new
authorization. Both preserve existing edits and keep Git operations,
installation and external publication
subject to your explicit authorization. A policy file or task record does not
grant permission.

## Project policy

Save preferences in `<project>/.ai-workflow/policy.json`:

```json
{
  "schema_version": 1,
  "mode": "collaborative",
  "review_level": "critical",
  "max_parallel_tasks": 2,
  "response_language": "en",
  "verification_notes": ["Run the relevant tests before delivery"]
}
```

| Field | Values and effect |
|---|---|
| `mode` | `collaborative` or `continuous`; controls collaboration pacing |
| `review_level` | `critical` or `all`; determines when independent review is attempted |
| `max_parallel_tasks` | Integer from 1 to 8; caps concurrent subtasks |
| `response_language` | `auto` or a language tag such as `en` or `zh-CN` |
| `verification_notes` | Up to 16 short project verification requirements |

`schema_version` must be `1`; the other fields may be omitted. Resolution order
is the selected packaged profile, then project settings, then explicit options
you provide for the current conversation. Invalid files or unknown fields
produce an error; correct the configuration before continuing dependent work.
See the [policy schema](../schemas/policy.schema.json).

## Inspect configuration

All commands below run from the installed CodeVow package root. Replace
`/path/to/project` with your actual workspace. The optional tools require
Python 3.11+; the Markdown skills themselves need no Python.

```sh
python3 tools/workflow_tool.py policy resolve \
  --plugin-root . --workspace /path/to/project
```

The result includes effective values, each value's source and a policy hash.
You can provide explicit options for the current task:

```sh
python3 tools/workflow_tool.py policy resolve \
  --plugin-root . --workspace /path/to/project \
  --mode continuous --review-level all --response-language en \
  --verification-note "Run the relevant tests before delivery"
```

Resolution is read-only. It does not save settings or authorize implementation.
Use `python3 tools/workflow_tool.py policy resolve --help` for all options.

## Optional task and evidence records

For long-running work or handoff, copy and adapt the [task input
template](../templates/task.json). Use the actual plan, protected paths and
references to your authorization; the tool records them without proving or
granting permission.

Preview creation first:

```sh
python3 tools/workflow_tool.py task create \
  --workspace /path/to/project --id my-task --input /path/to/task-input.json
```

Add `--apply` to that command to save the record. Records live in
`<project>/.ai-workflow/tasks/<id>/`. To check the record and its evidence:

```sh
python3 tools/workflow_tool.py task check --workspace /path/to/project --id my-task
```

Updates use the current `record_revision` from `task.json`, and an input file
following the [task schema](../schemas/task.schema.json):

```sh
python3 tools/workflow_tool.py task update \
  --workspace /path/to/project --id my-task \
  --expected-revision <current-revision> --input /path/to/update.json
```

Replace `<current-revision>` with the actual integer. Update is also a preview
unless you add `--apply`; a revision conflict requires reading the current
record before trying again. The [evidence template](../templates/evidence.json)
describes evidence inputs. `task check` detects changed evidence, files or
workspace identity rather than treating an earlier pass as current.

## Optional project file staging

Staging creates a workspace-local plugin copy. Native installation does not
require it. File staging needs a platform supporting POSIX file operations.

Generate a plan:

```sh
python3 tools/workflow_tool.py files plan \
  --package . --target /path/to/project --action stage --out /tmp/codevow-plan.json
```

This writes only the plan file. Read the plan and the reported `plan_hash`,
then apply the operation you have approved:

```sh
python3 tools/workflow_tool.py files apply \
  --plan /tmp/codevow-plan.json --expected-plan-hash <plan-hash>
```

Replace `<plan-hash>` with the reported hash. Copies go to
`<project>/.ai-workflow/staged/ai-code-workflow/`; ownership is recorded in
`<project>/.ai-workflow/receipts/ai-code-workflow.json`.
Use `files plan --action update` with the new package to update the copy.
Use `files plan --target /path/to/project --action remove --out /tmp/codevow-plan.json`
to plan removal, then inspect and apply that plan.

Updates and removals refuse to overwrite or delete files you have edited.
Interrupted operations preserve recovery material. Avoid concurrent edits
during apply and inspect any reported conflicts. Staging does not register a
plugin with the host; updating the host plugin does not update staged files.

The tools make no network or model calls, execute no project commands and
perform no Git operations. Use `python3 tools/workflow_tool.py --help` for
the command index.
