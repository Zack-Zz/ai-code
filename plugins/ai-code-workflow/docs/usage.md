# Using CodeVow

CodeVow is a set of six skills — `workflow`, `tdd`, `debugging`,
`review`, `verification`, plus the shared presentation contract
`review-results` — that organize how your coding assistant works with you.
Packages target Claude Code, Codex and ZCode; native behavior remains
unverified for each. Claude Code and ZCode reviewer declarations use the same
contract, inherited models and read-only tool lists; this is configuration
evidence until a real session confirms enforcement.

Default collaboration mode: **plan first, implement after your confirmation**.

This is the workflow plugin within [ai-code](../../../README.md). Its source
entry from the repository root is
`plugins/ai-code-workflow/scripts/workflow_tool.py`; installed examples below
run from the package root using `tools/workflow_tool.py`. Collection-level
list/validate/build/check commands are at `tooling/plugin_tool.py` in the
trusted repository, as described in [the authoring guide](../../../docs/plugin-authoring.md).

## The five abilities

| Skill | What it does | You say things like |
|---|---|---|
| workflow | Classifies your request (read-only vs development), forms a proportionate plan, tracks authorization and organizes the rest | "Add a bulk discount tier" |
| tdd | Drives behavior changes test-first: valid RED, minimal GREEN, refactor under a preserved baseline | (loaded automatically for development tasks) |
| debugging | Evidence-driven diagnosis: explicit hypotheses, minimal distinguishing experiments, no guess-editing loops | "This intermittently returns unknown — diagnose, don't shotgun-fix" |
| review | Risk-focused review of the final diff; attempts an independent read-only reviewer for critical risk; findings verified by the main agent | "Review this diff; treat it as high risk" |
| verification | Binds completion claims to the final code state with explicit verification levels and stale-evidence rules | (loaded before every delivery) |

`review-results` is not invoked by name: the review output is presented
through it (decision first, business flow, abnormal node, clickable evidence).

## Collaboration modes

- `collaborative` (default): development tasks get a plan proportionate to
  their size — QUICK and urgent fixes get a short plan, not none — and
  implementation starts after an applicable confirmation. Ordinary details
  are not re-asked once confirmed.
- `continuous`: same contracts, but inside a scope you have already
  explicitly authorized the agent keeps going without per-step
  re-confirmation. **Selecting continuous never creates authorization**; Git
  writes, installs and external publication always need their own explicit
  go-ahead, in both modes.

## Policies

Two profiles ship with the package (`policies/collaborative.json`,
`policies/continuous.json`) with fields `review_level` (critical|all),
`max_parallel_tasks` (1–8), `response_language` (auto or a language tag),
`verification_notes` (up to 16 short project requirements). A workspace may
override fields via `.ai-workflow/policy.json` (`schema_version: 1`, subset of
fields); your explicit in-conversation options win over the file.

Resolve what is in effect (read-only, no side effects):

```sh
python3 tools/workflow_tool.py policy resolve \
  --plugin-root /path/to/ai-code-workflow --workspace /path/to/your/project
# add --mode continuous --review-level all --max-parallel-tasks 3 \
#   --response-language zh-CN --verification-note "run full suite"
```

The output records the effective policy, a per-field source, warnings and a
content hash.

## Task records (optional, for long or hand-off tasks)

```sh
# start a record (preview first; add --apply to write)
python3 tools/workflow_tool.py task create --workspace . --id my-task \
  --input task-input.json            # schema: templates/task.json
python3 tools/workflow_tool.py task update --workspace . --id my-task \
  --expected-revision 1 --input update.json --apply
python3 tools/workflow_tool.py task check --workspace . --id my-task
```

Records live in `<workspace>/.ai-workflow/tasks/<id>/`. They are an audit
index: nothing in them grants permissions, and `task check` reports when
evidence has gone stale (edited evidence, changed files, drifted workspace)
instead of silently trusting old passes. Exit codes: 0 ok, 1 validation/run
failure, 2 arguments/data, 3 conflict/lock, 4 identity/evidence invalid,
5 host environment unavailable.

## What the tools never do

No Git mutations, no model calls, no project command execution, no background
services, no writes to your global config. Staging files into a project is an
explicit, receipted operation (see [installation](installation.md)) that refuses to
overwrite your edits and never takes over files it does not own.
