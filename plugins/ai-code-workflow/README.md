# AI Code Workflow

English | [简体中文](README.zh-CN.md)

A public, host-portable engineering workflow for AI coding assistants:
**plan first, test-first, evidence-driven debugging, risk-focused review, and
verification bound to the final code state.** First-release targets are
ZCode and Codex; Claude Code is planned later.

One source generates both host packages. The package ships six skills —
`workflow`, `tdd`, `debugging`, `review`, `verification`, and the shared
review-presentation contract `review-results` — plus two collaboration
policies (`collaborative` default, `continuous` pacing-only), task/evidence
record tooling, and receipted file staging. It contains no agent runtime, no
MCP scheduling, no background services, no model routing and no mandatory
multi-role pipeline.

**Status (2026-10-03): unpublished candidate bundles 2.0.0; implemented_with_acceptance_blocked.** Implemented
and deterministically tested; all seven measured core modules exceed 80% statement coverage.
real-host acceptance is blocked on the authoring machine and honestly marked
`unverified` — see [docs/support-matrix.md](docs/support-matrix.md) and
[evals/blocked-env-2026-10-02.md](evals/blocked-env-2026-10-02.md). Not yet
host-verified anywhere; do not cite it as such.

This directory is one plugin in the [ai-code collection](../../README.md).
Paths below are relative to this plugin directory unless a command explicitly
says to run from the repository root. Shared packaging and new-plugin guidance
are in [the authoring guide](../../docs/plugin-authoring.md).

## What it gives you

- **Plan-first collaboration** — every development task (QUICK and urgent
  included) gets a proportionate plan and waits for your confirmation;
  already-authorized scopes are not re-asked. Continuous mode only changes
  pacing inside an authorized scope — a mode switch never grants anything.
- **Real TDD discipline** — valid RED (environment failures never count),
  minimal GREEN, refactor under a preserved baseline.
- **Evidence-driven debugging** — explicit hypotheses and minimal
  distinguishing experiments; guessing stops after two evidence-free tries.
- **Honest review** — affected dimensions only, independent read-only
  reviewer attempted for critical risk, findings verified by the main agent,
  output presented through the review-results decision-first contract.
- **Verification that doesn't rot** — claims bind to the final code state;
  changed code invalidates stale passes; unresolved critical/high defects
  keep the task incomplete.
- **Audit trail without permission leakage** — optional task/evidence
  records with CAS updates and content-hash invalidation; records never
  generate authorization.

## Quick start

Unpublished yet (no marketplace release). Run from the ai-code repository root:

```sh
npm test
python3 tooling/plugin_tool.py validate --plugin ai-code-workflow
python3 tooling/plugin_tool.py build --plugin ai-code-workflow --host all --output dist-check
python3 tooling/plugin_tool.py package check \
  --path dist-check/zcode/ai-code-workflow --host zcode --root .
```

Install a built package into ZCode/Codex: [docs/installation.md](docs/installation.md).
Day-to-day usage and policies: [docs/usage.md](docs/usage.md).
The source-specific tool remains `plugins/ai-code-workflow/scripts/workflow_tool.py`
from the repository root; its installed entry remains `tools/workflow_tool.py`.
Policy/task/files behavior belongs to this plugin. Its ID and candidate version
remain `ai-code-workflow` and `2.0.0`.

## Plugin directory map

| Path | Purpose |
|---|---|
| `skills/`, `policies/`, `product.json` | The plugin source and its identity/whitelist |
| `scripts/workflow_tool.py`, `scripts/workflow/` | Management tools (validate/policy/task/build/package/files), Python 3.11+ stdlib only |
| `adapters/zcode/`, `adapters/codex/` | Host manifests, marketplace templates, interface metadata, capability notes |
| `schemas/`, `templates/` | Fixed data-contract documents and task/evidence input templates |
| `evals/` | A01–A25 acceptance cases, one-shot fixtures, prepare/collect/grade tooling |
| `../../dist/` | Generated host distributions at the repository root (rebuildable) |
| `docs/` | Design docs, usage, installation, migration, support matrix, coverage |
| `tests/` | Plugin Node contract checks and Python unit/integration tests; the unified gate lives at `../../tests/run-suite.js` |

## Verification & development

- Unified gate: `npm test` (`tests/run-suite.js`) — every group runs even if
  an earlier one fails; verdicts come only from process exit statuses (no
  output parsing); empty test sets fail.
- Workflow Python tests, from the repository root: `python3 plugins/ai-code-workflow/tests/run_python_tests.py`.
- Shared tooling Python tests: `python3 tests/run_python_tests.py`.
- Plugin skill contracts, from the repository root: `node plugins/ai-code-workflow/tests/skills/run-skills.js`.
- Lint: `npm run lint` (eslint + markdownlint; needs `npm install`).
- Coverage method and numbers: [docs/coverage.md](docs/coverage.md).
- Migrating from backend-engineering-lite: [docs/migration.md](docs/migration.md).

## License & provenance

MIT — see [LICENSE](LICENSE) and [NOTICE](NOTICE). This repository's early
history derives from Affaan Mustafa's ai-code (MIT); the v1 workflows migrate
from backend-engineering-lite (also in-repo history), whose license is
preserved in [LICENSES/backend-engineering-lite.txt](LICENSES/backend-engineering-lite.txt)
and in every package. BEL's README credited obra/Superpowers as the
inspiration for its evidence-driven workflow ideas; no source was copied.
