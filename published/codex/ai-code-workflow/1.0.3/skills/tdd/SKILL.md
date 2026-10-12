---
name: tdd
description: Use for authorized behavior changes after applicable plan confirmation; drive valid RED, minimal GREEN and refactor without turning diagnosis or review into repair
origin: ai-code-workflow
---

# TDD

Applies to features, bug fixes, executable scripts and any behavior change.

Before writing a test, use the [workflow request and authorization
context](../workflow/SKILL.md#request-and-authorization-context). Reuse it if
already established; otherwise read and establish it first. Diagnosis or
review findings do not authorize a test or repair. A request to add only a
reproduction test is still a development request: under `collaborative`,
present the test scope and wait for applicable plan confirmation before
writing it. The initial request is not confirmation of an unpresented plan.
After confirmation, a test-only grant permits the reproduction and RED
evidence, then a handoff; obtain broader authorization before GREEN or
production changes.

## RED — a valid failure first

1. Write the smallest observable-behavior test for the target behavior.
2. Run it and confirm the failure comes from the missing target behavior.
3. Invalid RED: the test passes immediately; a syntax error; a missing
   dependency or broken test environment. These are environment problems —
   report and resolve what is authorized, never count them as RED, and do not
   start implementation on top of a blocked RED.

If you catch yourself implementing first: protect all existing modifications,
separate precisely what can be separated, and return to the RED. Never reset
or checkout the whole workspace to undo.

## GREEN — minimal

Implement only what the current test requires, then run the affected tests.
Then REFACTOR under green; new behavior starts the next RED.

## Baselines

- Pure refactor: establish/confirm the existing-behavior green baseline
  first; refactor keeps it green. Do not manufacture an artificial RED.
- Documentation and configuration that do not change executed behavior use
  the appropriate structural validation instead.
- Repositories with pre-existing failures: only a baseline distinguishes
  historical from newly introduced failures; without evidence, do not guess
  attribution.

## Evidence

Record the command, exit status and the RED failure reason; bind every pass
claim to the final code state. Re-run and re-verify when related code or
tests change afterwards — a pass recorded against older code is stale.
