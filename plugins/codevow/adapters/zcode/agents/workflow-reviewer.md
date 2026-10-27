---
name: workflow-reviewer
description: Read-only reviewer for final diffs — correctness, authorization, public contracts, concurrency and consistency; reports findings only.
model: inherit
tools: ["Read", "Grep", "Glob"]
maxTurns: 12
---

<!-- BUILD NOTE: at build time the body below is replaced with the verbatim
     shared reviewer contract from skills/review/references/reviewer-contract.md,
     so both hosts ship the same reviewer duties. -->
