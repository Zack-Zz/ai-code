# Using CodeVow

English | [简体中文](usage.zh-CN.md)

After [installation](../../../docs/installation.md), start a new host session
and describe the goal, change scope and acceptance conditions. CodeVow
organizes planning, TDD, debugging, review and verification around that request.

## Choose a collaboration mode

The mode controls whether the assistant waits for you to confirm its proposed
plan before editing. Choose the working style you prefer:

| Mode | How work starts | Choose it when |
|---|---|---|
| `collaborative` — collaborative mode (default) | The assistant investigates, explains the proposed change and waits for you to confirm the plan before editing. | You want to review the approach before implementation. |
| `continuous` — continuous mode | After you ask it to implement a task, the assistant explains a short plan and proceeds within the scope you authorized. | The goal and scope are clear, and you want the assistant to carry the task through. |

For example, you ask: "Fix the login timeout, change only the authentication
module, and run its tests."

- In `collaborative`, the assistant investigates and proposes a fix, then waits
  for your confirmation before editing.
- In `continuous`, it investigates, explains a short plan, and carries out the
  fix and tests within the scope you specified.

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

Choose your default in [project policy](#project-policy), or tell the assistant
which mode to use for the current task. Selecting `continuous` alone does not
ask the assistant to implement anything; also describe the task and the changes
you want it to make.

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

Actively add or merge this snippet into your host's project instructions,
preserving existing content. CodeVow does not write configuration automatically.
The snippet assumes neither a fixed installation-cache path nor automatic
activation of a bundled `AGENTS.md`.

For ZCode, the native entries are global `~/.zcode/AGENTS.md` and `AGENTS.md`
at the current Workspace root. Add or merge the snippet into the Workspace-root
file for this project; ZCode does not scan subdirectories or expand `@include`.
`CLAUDE.md` is only offered for a one-time migration during onboarding, not
read as a native entry afterward. See [ZCode's AGENTS.md guide](https://zcode.z.ai/en/docs/agents).

CodeVow's `collaborative` and `continuous` are workflow instructions; they do
not switch ZCode's native execution mode or intercept its editing tools.
ZCode's Plan Mode can present a plan for confirmation before editing. This
setup guidance does not establish real-host acceptance: verify loading and
adherence in your actual session.

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
- For development, it follows the [selected mode](#choose-a-collaboration-mode)
  to explain the plan and start implementation.
- Behavior changes start with a meaningful failing test, followed by the
  implementation and refactoring under the passing baseline.
- Debugging uses hypotheses and small experiments to locate the cause.
- Review focuses on affected risks; an independent review is attempted for
  critical risk or when the configured review level is `all`.
- Delivery reports the final code state, actual checks, findings and remaining
  work. Changed code needs fresh verification.

## Working with subagents

CodeVow adds brief coordination guidance to the host's existing agent capabilities.
The assistant chooses sequential or parallel work based on dependencies, write
overlap and useful deliverables, within your instructions and the host's limits.

- Two independent modules with agreed interfaces can be implemented in parallel,
  then integrated and checked together.
- If a shared interface is still undecided, settle it before dependent
  implementation; unrelated work can continue meanwhile.

Delegated work needs enough context, a clear change scope and an expected result.
In a shared checkout, coordinate overlapping writes and preserve others' edits.
Separate workspaces can produce alternative patches for integration, but may
still share resources such as a database or port. Before taking over interrupted
work, check its actual state and partial changes. The main assistant checks the
returned artifacts and the integrated result; separate passing tests alone do
not establish that the complete change works.

`max_parallel_tasks` is an upper limit, not a target team size. Scheduling,
permissions and isolation come from the host; CodeVow does not create a required
agent pipeline, worktree or task record. Existing authorization and review rules
still apply.

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
| `mode` | `collaborative` (confirm the plan before editing, default) or `continuous` (proceed within the task scope you authorized); see [mode selection](#choose-a-collaboration-mode) |
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
`<project>/.ai-workflow/staged/codevow/`; ownership is recorded in
`<project>/.ai-workflow/receipts/codevow.json`.
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
