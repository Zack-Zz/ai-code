# Support matrix and current verification status

## Current package targets (2026-10-07)

| Target | Native package format | Runtime acceptance |
|---|---|---|
| Claude Code | .claude-plugin/plugin.json, .claude-plugin/marketplace.json and shared-contract reviewer | unverified; release acceptance is null |
| Codex | plugin.json, .agents/plugins/marketplace.json and six native skill interfaces | unverified; release acceptance is null |
| ZCode | .zcode-plugin/plugin.json, marketplace.json and shared-contract reviewer | unverified; release acceptance is null |

Claude Code is a newly declared package target. Official format references and
local script/package checks do not establish native loading or behavior. The
existing A25 scenario still covers Codex/ZCode; it is not three-host acceptance.
The dated evidence below retains its original scope, numbers and hashes.

Directory note (2026-10-07): this is the dated workflow baseline, now under
`plugins/ai-code-workflow/`. Original counts, commands and hashes below are
historical evidence; they do not validate the migration. Current navigation
and shared packaging are described in [the multi-plugin design](../../../docs/design/2026-10-07-multi-plugin-design.md).

Honest state as of 2026-10-03 (overall review repairs): the product is
**implemented with real-host acceptance blocked** on the authoring machine
(`implemented_with_acceptance_blocked`). Every capability below that depends
on a live host session is `unverified` — the packaging formats follow the
official packaging references and actual native probes; no complete host
acceptance matrix has passed. Native installation and
partial smoke observations are reported separately below.

## Deterministic verification (real, executed)

| Area | Evidence |
|---|---|
| Tool contracts (io/product/policy/state/build/package_check/owned_files) | 265 Python tests green via `npm test` (includes 33 eval-tool tests); runner self-tests 7/7 |
| Skill & case source contracts | 12 Node contract checks green (structure only, no model behavior claimed) |
| Package integrity & reproducibility | same-source builds produce identical content hashes and ZIP bytes; package check green for both hosts |
| Cross-host parity | shared skill and policy files byte-identical across ZCode/Codex packages |
| Manager/package acceptance (A23/A24/A25) | executed for real by `evals/grade.py`: install/repeat/update/remove, user-edit protection, un-owned file protection, real UPDATE interruption with exact recovery hashes and byte backups, concurrent-apply single-winner with published payload/receipt verification, two-host traceability — all `pass` |
| Tool statement coverage | 87.6% aggregate (docs/coverage.md), target ≥80% met |

[Overall review repair record](reviews/2026-10-03-review-fixes.md) includes the
21 findings, regression boundaries and final artifact hashes.

## Host capabilities

All current-bundle session capabilities remain `unverified`: discovery,
explicit invocation, automatic selection, policy loading, native subagents,
reviewer restrictions and workspace isolation. Reviewer instructions provide
`policy_only` enforcement until actual host restrictions are proven.

On 2026-10-02, both applications were found to bundle usable official CLIs
(Codex 0.159.2, ZCode 0.16.9). Codex native installation succeeded in a private
profile. ZCode native validation and marketplace registration succeeded, but
installation attempted an unauthorized ordinary-global config write. The
Codex model smoke could not read its skill file because nested sandbox setup
failed; an outer-sandbox retry was rejected by automatic approval review.
See [current probe details](../evals/blocked-env-2026-10-02.md) and
`adapters/*/capabilities.md`. These probes do not complete T07.

## What a real acceptance round must add

Per `docs/design/2026-10-01-workflow-v1-acceptance.md`: A01–A22 once per
host, the 12 critical cases three times each, native-vs-plugin comparisons
for A03/A11/A20, using `evals/prepare.py|collect.py|grade.py` with real
session material. Until then, do not cite this project as host-verified, and
keep external support statements to the deterministic rows above.

## Baselines

- Development/CI: Python 3.13 / Node 22 (per implementation spec); the round
  actually ran on Python 3.13.3 / Node 22.16.0 locally.
- Package format references fetched 2026-10-01: OpenAI plugin packaging
  guide; ZCode plugin docs (`.zcode-plugin/plugin.json`, marketplace schema).
