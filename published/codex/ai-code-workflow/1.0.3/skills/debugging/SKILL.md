---
name: debugging
description: Use when a coding symptom needs cause analysis; diagnose with hypotheses and evidence, then report before repair unless an applicable change is already authorized
origin: ai-code-workflow
---

# Debugging

Start from the phenomenon, not from a fix.

Use the [workflow request and authorization
context](../workflow/SKILL.md#request-and-authorization-context) before choosing
experiments; establish it first when invoked directly without valid context.
Investigation stays read-only unless the actual user authorized the particular
write. Finding the cause does not authorize tests, instrumentation or repairs.

## 1. Frame

Determine: the phenomenon, the expected behavior, the affected scope, recent
changes, and reproduction conditions. Separate what is observed from what is
assumed.

## 2. Experiment loop

For each minimal experiment, write down before running it:

- the hypothesis it distinguishes,
- the observation each outcome would produce,
- the actual result.

Two consecutive attempts that add no evidence mean stop editing. Return to
the hypothesis list and choose a different observation point instead of
guess-modifying code.

## 3. Boundaries

- Temporary diagnostic writes follow the same authorization rules as any
  other write.
- Manual recovery, an HTTP 200, or a coincidental pass never count as proof
  the root cause is fixed.
- Once located, report the evidence, impact, proposed change and verification
  scope. For an investigation without repair authorization, complete that
  report and wait for applicable confirmation before entering `tdd`.
  Within already-authorized development, proceed through `tdd` with the
  permitted reproduction, fix and regression checks. Respect test-only grants
  and confirm material scope extensions before writing outside the grant.

## 4. Hand-off

Report confirmed facts, remaining hypotheses, and the evidence trail. Mark
environment-caused blockers as environment issues, not as verified root
causes.
