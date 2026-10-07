# ai-code

English | [简体中文](README.zh-CN.md)

A repository for AI-related plugins. Each plugin owns its source, identity,
version, resources, tests and support claims. Shared tooling registers plugins,
validates their source, builds reproducible host packages and generates a local
marketplace. Plugin behavior stays within its own directory.

The first plugin is **AI Code Workflow** (`ai-code-workflow`), an engineering
workflow for AI coding assistants. More plugin types can be added when their
requirements are concrete; the repository does not impose workflow skills,
policies or task records on every plugin.

## Plugins

| Plugin | Purpose | Version and support |
|---|---|---|
| [AI Code Workflow](plugins/ai-code-workflow/README.md) | Planning, TDD, debugging, review, verification and delivery evidence | Unpublished candidate `2.0.0`; [real-host acceptance remains unverified](plugins/ai-code-workflow/docs/support-matrix.md) |

`catalog.json` registers plugin directories. Each directory's `product.json`
is the sole source of its plugin ID, version and resource whitelist. The root
private Node package is maintenance tooling; its version is not a plugin
release version.

## Quick start

Run from the repository root with Python 3.11+ and Node 22+:

```sh
python3 tooling/plugin_tool.py list
python3 tooling/plugin_tool.py validate --all
npm test
python3 tooling/plugin_tool.py build --all --host all --output dist-check
python3 tooling/plugin_tool.py package check \
  --path dist-check/codex/ai-code-workflow --host codex --root .
```

The output directory must be absent or empty. To work on one plugin, replace
`--all` with `--plugin ai-code-workflow`. `--host` accepts `zcode`, `codex` or
`all`; only declared hosts are built for each selected plugin.

A distribution contains a shared local marketplace named `ai-code-local`,
individual plugin packages and individual ZIPs. Each ZIP contains only its
plugin and a matching single-plugin marketplace. Unzip to a stable directory,
then register and install through the host's native plugin system. See the
plugin's [installation guide](plugins/ai-code-workflow/docs/installation.md).

Source checks and package integrity checks do not certify native loading or
model behavior. Host acceptance and its evidence belong to each plugin.

## Repository map

| Path | Purpose |
|---|---|
| `catalog.json` | Explicit list of registered plugin directories |
| `plugins/<id>/` | Self-contained plugin source, manifest, resources, adapters, tests and documentation |
| `tooling/plugin_tool.py` | Shared list, validate, build and package-check entry point |
| `tooling/` | Shared source validation, packaging and marketplace generation |
| `tests/` | Shared tooling tests and the unified test runner |
| `docs/plugin-authoring.md` | How to add a plugin and declare its supported hosts |
| `docs/design/2026-10-07-multi-plugin-design.md` | Multi-plugin boundaries, contracts and migration plan |
| `dist/` | Generated distributions, rebuildable from registered sources |

## Development

- Read the root `AGENTS.md` and the plugin's local instructions before editing.
- Behavioral changes use meaningful RED then GREEN tests. Run `npm test` for
  the shared tooling and every registered plugin's test groups.
- Run `npm run lint` after installing local maintenance dependencies.
- Keep plugin IDs and versions independent, whitelist every packaged resource
  and preserve the source/hash boundary between plugins.
- Use [the authoring guide](docs/plugin-authoring.md) for a minimal addition.
  New runtime integrations require their own design and host verification.

AI Code Workflow's policy resolution, task records and receipted file staging
remain at `plugins/ai-code-workflow/scripts/workflow_tool.py` in the source and
`tools/workflow_tool.py` in its package. These are workflow-specific tools.

## License and provenance

MIT — see [LICENSE](LICENSE) and [NOTICE](NOTICE). The repository's early history
derives from Affaan Mustafa's ai-code. AI Code Workflow's migration history and
preserved backend-engineering-lite license are documented in its
[README](plugins/ai-code-workflow/README.md) and
[migration guide](plugins/ai-code-workflow/docs/migration.md).
