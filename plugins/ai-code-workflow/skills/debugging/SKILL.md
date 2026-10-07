---
name: debugging
description: Diagnose with evidence - explicit hypotheses, minimal distinguishing experiments, no guess-editing loops
origin: ai-code-workflow
---

# Debugging

Start from the phenomenon, not from a fix.

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
- Once located, produce the input for `tdd`: a failing test that reproduces
  the defect, then the fix, then regression checks covering the failure path
  and its boundaries.

## 4. Hand-off

Report confirmed facts, remaining hypotheses, and the evidence trail. Mark
environment-caused blockers as environment issues, not as verified root
causes.
