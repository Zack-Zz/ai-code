---
name: workflow-reviewer
description: Read-only reviewer for final diffs — correctness, authorization, public contracts, concurrency and consistency; reports findings only.
model: inherit
tools: Read, Grep, Glob
maxTurns: 12
---

<!-- BUILD NOTE: the shared reviewer body is composed from
     skills/review/references/reviewer-contract.md during packaging. -->
