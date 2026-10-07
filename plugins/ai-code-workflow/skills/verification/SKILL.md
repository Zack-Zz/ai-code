---
name: verification
description: Bind every completion claim to the final code state with explicit verification levels and stale-evidence rules
origin: ai-code-workflow
---

# Verification

Use the effective policy from workflow, including `verification_notes` and
`response_language`. A direct invocation without that context first resolves
it through [workflow](../workflow/SKILL.md). Project notes are validation
requirements, not permission to run arbitrary commands.

Every completion claim binds to the final code state — verified after the
last relevant change, not before.

## Levels

Report only the levels actually reached, in this order; a task need not
mechanically reach the highest one, and tool reachability is never business
success:

1. Source review — the final diff was read and understood.
2. Static/compile — lint/typecheck/build passed on the final state.
3. Tests — the relevant suites ran and passed on the final state.
4. Service reachability — the running service answers (for service changes).
5. State/persistence — data and state effects confirmed where applicable.
6. Business result — the user-visible behavior the task existed for.

## Stale evidence

Any later change to related code or tests invalidates the corresponding pass
records: re-judge the affected range and re-verify. Evidence binds via the
actual content hashes of code, tests and raw captures — existence of a file
is not validity.

## Delivery content

Deliverables: behavior effect; this-change diff (user's pre-existing edits
kept separate); actual verification per level with commands and exit
statuses; review and issue handling; failures, not-run items and blockers
stated as such; remaining operations. Unresolved confirmed critical/high
defects keep the task incomplete — other green checks do not offset them.

Delivery hands the change to the user for review; it never triggers commit,
push or publication on its own.
