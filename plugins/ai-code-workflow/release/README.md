# CodeVow — AI Coding Workflow

CodeVow helps an AI coding assistant plan with you, use TDD, diagnose from
evidence, review risks and verify the final code state. Its plugin ID is
`ai-code-workflow`. This package is a self-hosted preview candidate; the generated
manifest and release record supply its version and hashes.

[简体中文](README_CN.md)

## What the package contains

Six Markdown skills: `workflow`, `tdd`, `debugging`, `review`, `verification`
and `review-results`. Two policies, `collaborative` and `continuous`, govern
collaboration pacing. Optional local Python tools resolve policy, keep
workspace-bound task/evidence records and stage owned files with receipts.
Claude Code and ZCode packages include a reviewer with `model: inherit`,
`Read/Grep/Glob` tools and `maxTurns: 12`, composed from the same reviewer
contract. Codex supplies the six native skill interface files.

Claude Code, Codex and ZCode package layouts are provided. **Every native host
acceptance is unverified**: packaging, hashes and script tests do not prove
skill discovery, automatic invocation, policy loading or reviewer enforcement.
Use a fresh, explicitly authorized host session to verify those behaviors.

Task host-run evidence accepts all three targets. In the source repository,
A23/A24 exercise each selected package's file staging and recovery tools, and
A25 checks all declared host packages and common resource hashes. These are
deterministic tool/package checks; they do not install into a host or run a
model. The evaluation scripts themselves are source-only developer tools.

## Dependencies, network and writes

Use your own host installation, account and selected model. Native Markdown
skills need no Node.js or Python runtime. Optional management commands require
Python 3.11+ and the standard library, on a platform with POSIX directory-handle
and no-follow file primitives for controlled reads/writes. Support outside the
validated development environment remains unverified. The package includes no external Python
or Node dependency, MCP server, background service or model router.

The Python tool makes no network/model calls and performs no Git mutations.
The host may use its normal model service and may download/update plugin
content during native installation; this remains subject to your host settings.
Native installation writes host-managed plugin/configuration locations.
CodeVow's explicit `task ... --apply` writes only the selected workspace's
`.ai-workflow/tasks/`; `files apply` writes owned files under
`.ai-workflow/staged/ai-code-workflow/` plus receipts/backups. A task record,
mode change or approved marker never grants user authorization.

## Install through the native host

The 1.0.2 candidate separates native installers from manual download packages.
A schema 2 release bundle contains `installers/ID-VERSION-HOST-plugin.zip`,
with one plugin root and its complete native package, including `artifact.json`.
It contains no local marketplace. The manual `downloads/ID-VERSION-HOST.zip`
still includes a marketplace; submission ZIPs remain separate source kits.

The planned GitHub preview market is `ai-code-preview` on
`codex/marketplace-preview`; stable is `ai-code-stable` on `codex/marketplace`.
Claude uses a fixed Release archive URL/hash, ZCode uses a ZIP URL/hash/path,
and Codex uses a version directory pinned to a distribution commit.
Publication and reviewed market deployment are separate steps. These notes do
not claim that either channel is remotely published or that native transport
and upgrades have passed acceptance. Existing `dist/` and `ai-code-local`
entry points remain during migration; use the source repository's publishing
guide for the current channel status.

For manual testing, download the local-market candidate for your host and unzip it to a stable directory.
The host marketplace root is the directory containing the native market file,
not the `ai-code-workflow` package directory. Default generated market name:
`ai-code-local`; use the actual declared name if you received a different source kit.

For Claude Code, the marketplace file is `.claude-plugin/marketplace.json`:

```sh
claude plugin marketplace add /path/to/extracted/claude
claude plugin install ai-code-workflow@ai-code-local
```

For Codex, the marketplace file is `.agents/plugins/marketplace.json`:

```sh
codex plugin marketplace add /path/to/extracted/codex
```

Restart the supported desktop client, select the `ai-code-local` source in
the Plugins Directory, and install CodeVow. Check your actual Codex version's
`plugin --help`; CLI availability varies. For ZCode, register the extracted `marketplace.json` through its native
marketplace UI and install `ai-code-workflow`. No automatic installer runs from
this package. Installation/enablement alone is not runtime acceptance.

Start a new session, confirm discovery and the installed package hash, then
try a small authorized development task. Confirm that planning, real RED/GREEN,
review and final-state verification actually occur before relying on the workflow.

## Optional commands from the package root

```sh
python3 tools/workflow_tool.py policy resolve --plugin-root . --workspace /path/to/project
python3 tools/workflow_tool.py task create --workspace /path/to/project --id demo --input templates/task.json
python3 tools/workflow_tool.py task check --workspace /path/to/project --id demo
```

Task creation is a preview unless `--apply` is explicitly added. For optional
file staging, first write and inspect a plan:

```sh
python3 tools/workflow_tool.py files plan --package . --target /path/to/project --action stage --out /tmp/codevow-plan.json
python3 tools/workflow_tool.py files apply --plan /tmp/codevow-plan.json --expected-plan-hash <actual-plan-hash>
```

File updates and removals reject user-edited/unowned content. Interrupted
operations retain recovery material. Staging is separate from host installation.
Verify a downloaded package using trusted repository tooling before executing
its Python code; the examined package must not serve as its own initial verifier.

## Source, license and limitations

Source: [Zack-Zz/ai-code](https://github.com/Zack-Zz/ai-code), plugin directory
`plugins/ai-code-workflow/`. Publisher metadata is a maintainer declaration,
not a verified identity or endorsement. Public release/promotion requires
separate approval and real acceptance for each claimed host.

MIT; see [LICENSE](LICENSE), [NOTICE](NOTICE) and the preserved
[backend-engineering-lite license](LICENSES/backend-engineering-lite.txt).
Historical workflow evidence and the support matrix remain in the source
repository, with their original dates. This candidate adds no claims of native
host acceptance and no automated trading, deployment or Git-publishing capability.
