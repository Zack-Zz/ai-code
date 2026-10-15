---
name: review
description: Use for standalone code review or risk review during authorized development; report verified findings, and repair only within an existing applicable grant
origin: ai-code-workflow
---

# Review

Inputs: the goal, constraints, final diff, verification records and the
change's authorship (pre-existing user edits vs. this change).

Use the [workflow request and authorization
context](../workflow/SKILL.md#request-and-authorization-context) and the effective
policy and its sources. If invoked directly without them, establish the
request/authorization context and resolve the policy first; do not assume
`review_level=critical`. A standalone review reports findings and proposed
fixes; it does not authorize tests or repairs.

## Scope

Check only the affected dimensions — correctness, authorization, public
contracts, concurrency, consistency — including interfaces between separately
developed parts. Do not load generic framework tutorial libraries and do not
review unrelated code.

## Independent review

Attempt an available independent reviewer when risk is `critical` or
`review_level=all`:

- Give it a clear scope, the requirements, the diff and the evidence. Respect
  the user's existing host, role and model settings; prefer the host's read-only
  restriction when one actually exists.
- If the restriction is instruction-level only, mark the attempt
  `policy_only` — never claim the host blocks writes when it does not.
- Reviewer unavailable or the call failed: state the concrete reason, your
  self-review scope, and what remained uncovered. Self-review is never
  described as independent review.

Delegation alone does not require a separate reviewer for every subtask.
An implementer's check of its own changes remains self-review.

The reviewer only reports findings. The main agent verifies each one and
reports evidence, impact and proposed changes. During already-authorized
development, fix confirmed issues within the approved objective and re-verify
the affected range. For standalone review or scope extensions, wait for
applicable repair authorization and plan confirmation before writing.

## Findings

Separate: confirmed defects (with evidence), unverified risks (with what
would verify them), and suggestions. An unverified risk is not promoted to a
confirmed defect by severity label alone; blocking depends on the task's
requirements and the actual evidence, and the rationale is stated.

Present the final output through the shared `review-results` skill. A
confirmed critical/high defect within the authorized development objective
keeps that change incomplete until resolved. A standalone review is complete
when its findings and limits are reported; unrepaired defects block the
relevant code delivery, not completion of the read-only review.

Read-only reviewer duties are shared across hosts in
[references/reviewer-contract.md](references/reviewer-contract.md); hosts
provide their own tool restrictions around it.
