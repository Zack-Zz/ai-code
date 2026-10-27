# ai-code architecture and responsibilities

English | [简体中文](architecture.zh-CN.md)

ai-code hosts independent AI coding plugins. Shared tooling handles registration,
validation, builds, package checks and distribution. Each plugin owns its features,
configuration and behavior rules. Start with the [development guide](../CONTRIBUTING.md).

## Repository structure

```text
ai-code/
  catalog.json                    Registered plugin directories
  distribution.json               Main marketplace and host transports
  plugins/
    codevow/             CodeVow
    ai-agent-delegation/          Agent Delegation
    codestack/      CodeStack
  tooling/plugin_tool.py          Shared CLI
  tooling/plugin_tools/           Validation, builds, checks and releases
  tests/                          Shared tests and the plugin test runner
  docs/                           User, development and maintenance guides
  published/                      Release records, receipts and Codex installation content
  .github/workflows/              CI, releases and marketplace synchronization
```

Build output goes to an explicitly selected empty temporary directory. `dist/`
is ignored by Git and is not maintained as source.

## Shared tooling and plugins

| Component | Owns |
|---|---|
| `catalog.json` | Relative plugin directory paths, without copied versions or resources |
| Plugin `product.json` | Plugin ID, name, version, hosts, attribution and resource whitelist |
| Plugin directory | Skills, configuration, helper tools, host adapters, guides and behavior tests |
| Shared tooling | Native manifests, packages, marketplaces, ZIPs and hashes generated from trusted source |
| Root `npm test` | Independent test groups for shared tooling and every registered plugin |

The root `package.json` configures private maintenance tooling, rather than a
plugin release version. Unregistered plugins are excluded from shared builds.
Packaged files must belong to the plugin's explicit resource whitelist.

Common resources have matching hashes across the same plugin's host packages;
host adapters and generated resources are declared separately. One plugin's rules
do not govern another. Shared tooling does not require every plugin to adopt
CodeVow's six skills, reviewer, policies or `.ai-workflow` task records.

## Marketplace and releases

Source and the public marketplace use `Zack-Zz/ai-code` at `main`. The marketplace
name is `ai-code`. Each plugin ID points to its latest successfully
synchronized stable release.

Local packages have separate names so registering a development source does not
reuse the public marketplace identity:

| Marketplace name | Source and purpose |
|---|---|
| `ai-code` | Public main marketplace |
| `ai-code-local` | Shared builds and Release downloads with a local marketplace |
| `codevow-local` | CodeVow's standalone build helper; local trials only |

| Input or output | Purpose |
|---|---|
| `product.json` | Current development version and resources |
| `published/index.json` | Synchronized stable versions and record references |
| `published/releases/ID/VERSION.json` | Stable release, frozen source and artifact records |
| `published/marketplaces.lock.json` | Managed public manifests and hashes |
| `published/codex/ID/VERSION/` | Content required for Codex installation |

Development and marketplace versions may differ. `marketplace sync --output <empty-directory>`
generates a development marketplace; `marketplace check` reads the public snapshot.
Development source is not used directly as a stable marketplace entry. Versions
use `X.Y.Z` or `X.Y.Z-preview.N`. Previews are GitHub Prereleases; stable versions
enter the marketplace after successful publication and synchronization.

Claude Code and ZCode install from fixed Release assets. Codex uses managed
installation content pinned to an actual distribution commit. Marketplace deployment
first prepares the Codex installation directory, then updates release records,
current pointers, root manifests and receipts. Changes to paths, bytes or the
base commit stop deployment.

The single manual build/publish entry uses trusted tooling from main to freeze
the committed plugin version and derive its canonical tag. Build performs remote
read-only checks and exports native installers. Publish creates or reuses the
immutable tag, uploads, reads back and publishes assets through `plugin-release`.
Stable publication automatically invokes marketplace synchronization.
Planning is read-only; deployment writes after approval in `plugin-marketplace`.
Host acceptance is an independent factual status, not a technical publication gate.
See the [publishing guide](publishing.md) and [evidence contract](release-evidence.md).

## Plugin hosts and execution engines

A host is the coding assistant that loads a plugin. An execution engine is an
independent session started or resumed by Agent Bridge. Their identifiers differ:

| Plugin host ID | Coding assistant | Bridge engine ID |
|---|---|---|
| `claude` | Claude Code | `claude-code` |
| `codex` | Codex | `codex` |
| `zcode` | ZCode | `zcode` |

For example, loading Agent Delegation in Codex and handing a task to Claude Code
uses different host and target engines. A same-tool handoff requires an explicit
request for an independent session.

The [rendering module](../tooling/plugin_tools/rendering.py) owns native package
and marketplace paths. Current Codex release checks use a skills-only profile.
New component types need a separate design for loading, permissions and channel requirements.

## Relationship with ai-mcp

The `@ai-mcp/agent-bridge` module in [ai-mcp](https://github.com/Zack-Zz/ai-mcp)
manages independent sessions, task recovery, process control and artifact access.
ai-code's `ai-agent-delegation` plugin supplies handoff skills, contracts and a
thin client for the external Bridge.

```text
The user explicitly names the task and target tool
  → Agent Delegation prepares the handoff
  → agent-bridge/v1 CLI
  → Agent Bridge manages the task and independent target session
  → Status, changes and verification results return
  → The originating session checks results against the original request
```

| Responsibility | ai-code | ai-mcp |
|---|---|---|
| Handoff entry | Establish user intent, target, scope and task requirements | Check caller identity and execution permissions |
| Calls and results | Consume the Bridge contract and present status and artifacts | Provide CLI/API, engine discovery, task and artifact operations |
| Execution and recovery | Continue and collect results using exact task IDs | Manage sessions, processes, state, recovery and cancellation |
| Resources | Plugin skills, thin client, adapters and packages | Engine drivers, runtime and controlled configuration |

The plugin does not duplicate engine drivers, credentials or the local task service.
The target tool manages its own model and account. Handoffs run only on an explicit
user request; ordinary development and native subagents keep their usual behavior.

For runtime setup, see [Agent Bridge](https://github.com/Zack-Zz/ai-mcp/blob/main/packages/agent-bridge/README.md).
For plugin usage, see [Agent Delegation](../plugins/ai-agent-delegation/README.md).

## Native DSH bundles and publication state

`dsh` is a fourth plugin host, not an Agent Bridge engine. CodeStack contributes
only a standard skill-filesystem provider. CodeVow adds a native spawn tool and
independent Reviewer preset; its scoped guard restricts native tools and does
not implement a second agent loop. Installed bundle metadata uses DSH locales.

Current source IDs `codevow`/`codestack` are separate from the immutable old public
records. Replacement mappings in trusted distribution configuration become
permanent retirement facts only after a successful stable update. DSH native
installation bytes live at `published/dsh/ID/VERSION/`; its plugin index is
`published/dsh/index.json`. Schema-3 Git installations bind each host to an
actual installation commit. A staged receipt makes the intermediate D state
verifiable before the marketplace C update. Historical snapshots remain readable.
