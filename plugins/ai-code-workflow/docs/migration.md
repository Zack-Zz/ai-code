# CodeVow migration and provenance

## CodeVow initial version (2026-10-07)

The maintainer confirmed that the new plugin had not been installed and chose
`1.0.0` as CodeVow's initial version. Plugin ID `ai-code-workflow` and market
`ai-code-local` remain unchanged. The preceding `2.0.0` candidate and the dated
records below are preserved as history; this is a one-time initialization,
not an update path for installed 2.0.0 copies. Existing BEL 0.1.1 installations
are separate plugins and are not modified by this source change.

Future installed releases use increasing semantic versions. The existing
immutable-content and downgrade checks remain in force. All real-host
acceptance remains unverified.

## Claude package and release metadata (2026-10-07)

The current source declares Claude Code, Codex and ZCode, with a separate
native Claude adapter at `adapters/claude/`. All host packages keep plugin ID
`ai-code-workflow` and candidate version `2.0.0`. Publisher metadata supplies
native author/developer fields; the PNG/SVG branding and curated package guides
are explicit whitelist resources. `release.json` leaves each host acceptance
slot null, so draft metadata is not evidence for stable promotion.

Existing policy/task/files records and authorization boundaries are unchanged.
The original A25 manager/package scenario remains a Codex/ZCode matrix. Its
historical result does not prove the new Claude adapter or a three-host model
behavior round. Original reports, dates, counts and hashes remain historical.

## Display name change (2026-10-07)

The active display name is now **CodeVow — AI Coding Workflow** (中文：
**CodeVow · AI 编码工作流**), previously AI Code Workflow. Plugin ID
`ai-code-workflow`, candidate version `2.0.0`, package paths, skill names and
policy/task/files contracts remain the same. The candidate is intended for self-hosted preview distribution;
real-host support remains `unverified`.

Source manifests, host descriptions, interface labels and active usage guides
use CodeVow. The dated v1 designs, probe reports and historical tables below
keep the original AI Code Workflow name and evidence. Renaming the brand does
not rewrite old hashes or turn prior probes into current acceptance.

## Migration from backend-engineering-lite (2026-10-01)

Status: **completed for the repository** on 2026-10-01 during the v1
development round. The old in-repo entry `zcode-workflow/` was removed after
the migration below landed and the new gate passed. **User installations are
untouched**: if you have the old `backend-engineering-lite` plugin installed
or its global rules in `~/.zcode/AGENTS.md`, nothing in this repository
removes or modifies them — remove them yourself when you adopt v1.

## Multi-plugin directory migration (2026-10-07)

The original workflow source directories, tests and docs now live under
`plugins/ai-code-workflow/`. Paths in the historical content mapping below
are relative to that plugin directory; they describe the 2026-10-01 BEL
migration. Plugin ID `ai-code-workflow`, candidate version `2.0.0`, installed
`tools/workflow_tool.py` and user-project `.ai-workflow` paths remain the same.

The collection's shared entry is `tooling/plugin_tool.py` from the repository
root. `catalog.json` registers the workflow directory, and its local
`product.json` owns the version independently of the root private Node package.
Shared builds generate `ai-code-local` aggregate markets and schema-version-2
indexes; the plugin-specific build remains available for existing single-plugin
flows. See [the current design](../../../docs/design/2026-10-07-multi-plugin-design.md).
This migration adds no new host-acceptance evidence and changes no user installs.

## Identity change

| | backend-engineering-lite | AI Code Workflow (v1) |
|---|---|---|
| plugin id | `backend-engineering-lite` | `ai-code-workflow` |
| version | 0.1.1 | 2.0.0 (release candidate, unpublished) |
| hosts | ZCode (user-level + plugin) | ZCode + Codex packages from one source |
| policy | embedded in prose | `policies/collaborative.json` / `continuous.json` + resolver |

The ids deliberately differ so a v1 package can never overwrite an old BEL
installation.

## Content mapping

| BEL source (zcode-workflow/) | v1 destination | Notes |
|---|---|---|
| `skills/bel-task-flow` | `skills/workflow` + `skills/tdd` | plan-confirm flow and risk levels generalized; language-neutral |
| `skills/bel-tdd` | `skills/tdd` | valid-RED rules kept; QUICK/urgent unified with the same plan requirement |
| `skills/bel-debugging` | `skills/debugging` | hypothesis/experiment loop kept |
| `skills/bel-verification` | `skills/verification` | verification levels + stale-evidence rules |
| `skills/bel-backend-review` | `skills/review` + `skills/review/references/reviewer-contract.md` | reviewer duties shared by both hosts |
| `agents/bel-backend-reviewer.md` | `adapters/zcode/agents/workflow-reviewer.md` (frontmatter) + shared contract body | model=inherit, tools Read/Grep/Glob, maxTurns=12 preserved |
| `manage_rules.py` (global `~/.zcode/AGENTS.md` writer) | **retired, not migrated** | v1 does not write user global rules |
| `manage_components.py` (user-level component install) | `scripts/workflow_tool.py files plan/apply` + adapters | ownership, receipts, user-edit protection replace hash manifests |
| `.zcode-plugin/plugin.json`, `marketplace.json` | `adapters/zcode/` templates → generated per build | version injected from `product.json` |
| — | `adapters/codex/` (new) | portable plugin.json + `.agents/plugins/marketplace.json` semantics |
| `templates/AGENTS.md`, `templates/user-rules.md` | **retired** | replaced by this repo's root `AGENTS.md` and the workflow skill |
| `examples/acceptance/{labels,auth,test_baseline}.py`, `user-note.txt` | `evals/fixtures/python_labels/`, `evals/fixtures/python_auth/` | one-shot v1 fixtures; grader assertions are separate |
| `ACCEPTANCE.md`, `VERIFICATION.md`, `evidence/` | `docs/bel-history/` | historical records only — not v1 acceptance evidence |
| `tests/` (20 tests) | superseded by `tests/workflow/` (contract-driven) | different scope: v1 tests cover the tool contracts |
| `plugins/backend-engineering-lite/LICENSE` | `LICENSES/backend-engineering-lite.txt` (+ every package) | with provenance header |
| `README.md` | superseded by v1 `README.md` / `README.zh-CN.md` / `docs/` | old text preserved in the B0 snapshot |

## Where the removed source lives

The complete pre-removal copy of `zcode-workflow/` lives outside the
repository in a durable author-local snapshot
(`ai-code-v1-snapshots/zcode-workflow/`, SHA-256 manifest
`zcode-workflow-SHA256SUMS` alongside it; copied from the B0 baseline
snapshot of 2026-10-01). Git history never tracked it. Historical BEL
acceptance/verification records are in-repo at `docs/bel-history/`
(historical only, not v1 evidence).

## Behavioral changes to know before adopting v1

- v1 requires a plan confirmation for every development task (including
  QUICK/urgent — a proportionally short plan); old BEL 0.1.1 skill text
  allowed QUICK to skip planning. The v1 skills and the acceptance matrix
  (A02–A04) follow the stricter rule.
- v1 ships a policy resolver (`policy resolve`) instead of prose-only
  defaults; `continuous` mode only changes pacing inside an already
  authorized scope.
- v1's reviewer is invoked through host adapters; if a host cannot enforce a
  read-only tool restriction the attempt is reported `policy_only`, never as
  an enforced sandbox (see `adapters/*/capabilities.md`).
