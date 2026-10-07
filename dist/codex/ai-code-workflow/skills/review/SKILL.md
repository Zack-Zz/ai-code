---
name: review
description: Risk-focused review of the final change with an independent reviewer when required, findings verified by the main agent
origin: ai-code-workflow
---

# Review

Inputs: the goal, constraints, final diff, verification records and the
change's authorship (pre-existing user edits vs. this change).

Use the effective policy and its sources supplied by workflow. If invoked
directly without them, first use the policy-loading section in
[workflow](../workflow/SKILL.md); do not assume `review_level=critical`.

## Scope

Check only the affected dimensions — correctness, authorization, public
contracts, concurrency, consistency. Do not load generic framework tutorial
libraries and do not review unrelated code.

## Independent review

Attempt an available independent reviewer when risk is `critical` or
`review_level=all`:

- Give it a clear scope, the requirements, the diff and the evidence; it
  inherits the current model; prefer the host's read-only restriction when
  one actually exists.
- If the restriction is instruction-level only, mark the attempt
  `policy_only` — never claim the host blocks writes when it does not.
- Reviewer unavailable or the call failed: state the concrete reason, your
  self-review scope, and what remained uncovered. Self-review is never
  described as independent review.

The reviewer only reports findings; the main agent verifies each one, fixes
what is confirmed, and re-verifies the affected range after fixing.

## Findings

Separate: confirmed defects (with evidence), unverified risks (with what
would verify them), and suggestions. An unverified risk is not promoted to a
confirmed defect by severity label alone; blocking depends on the task's
requirements and the actual evidence, and the rationale is stated.

Present the final output through the shared `review-results` skill. A
confirmed critical/high defect keeps the change not done until resolved.

Read-only reviewer duties are shared across hosts in
[references/reviewer-contract.md](references/reviewer-contract.md); hosts
provide their own tool restrictions around it.
