# ai-code

English | [简体中文](README.zh-CN.md)

A repository for AI-related plugins. Each plugin owns its source, identity,
version, resources, tests and support claims. Shared tooling registers plugins,
validates their source, builds reproducible host packages and generates a local
marketplace. Plugin behavior stays within its own directory.

The first plugin is **CodeVow — AI Coding Workflow** (`ai-code-workflow`),
an engineering workflow for AI coding assistants. More plugin types can be added when their
requirements are concrete; the repository does not impose workflow skills,
policies or task records on every plugin.

## Plugins

| Plugin | Purpose | Version and support |
|---|---|---|
| [CodeVow](plugins/ai-code-workflow/README.md) | Planning, TDD, debugging, review, verification and delivery evidence | Self-hosted preview candidate `1.0.2`; [real-host acceptance remains unverified](plugins/ai-code-workflow/docs/support-matrix.md) |

`catalog.json` registers plugin directories. Each directory's `product.json`
is the sole source of its plugin ID, version and resource whitelist. The root
private Node package is maintenance tooling; its version is not a plugin
release version.

## Install CodeVow from a Release

Open [CodeVow 1.0.2](https://github.com/Zack-Zz/ai-code/releases/tag/ai-code-workflow%2Fv1.0.2)
and download the ZIP for your host from **Assets**. No source checkout or build
is needed for these packages. This is a prerelease; real-host acceptance is
still unverified.

| Host | Download asset |
|---|---|
| Claude Code | `ai-code-workflow-1.0.2-claude.zip` |
| Codex | `ai-code-workflow-1.0.2-codex.zip` |
| ZCode | `ai-code-workflow-1.0.2-zcode.zip` |

Download `SHA256SUMS` too. Compare the ZIP's SHA256 with its
`downloads/<asset-name>` entry before extracting; on macOS/Linux, for example:

```sh
shasum -a 256 ~/Downloads/ai-code-workflow-1.0.2-zcode.zip
```

Extract into a permanent directory, keeping hidden files. Each download ZIP
contains `ai-code-workflow/` and an `ai-code-local` marketplace. Then:

- **Claude Code:** run `claude plugin marketplace add /path/to/extracted/claude`,
  then `claude plugin install ai-code-workflow@ai-code-local`.
- **Codex:** run `codex plugin marketplace add /path/to/extracted/codex`, restart
  your supported desktop client, and install CodeVow from the `ai-code-local`
  marketplace in its plugin directory. Check `codex plugin marketplace --help`
  if your CLI differs.
- **ZCode:** in the plugin settings, add the extracted `marketplace.json` or its
  containing directory as a marketplace, then install and enable CodeVow.

Replace each example path with the directory where you extracted that host's
ZIP. Start a new host session and confirm the plugin loads. Assets ending in
`-plugin.zip` contain only the plugin and are intended for marketplace
distribution; they do not contain the local marketplace used above. GitHub's
automatic **Source code** downloads are development sources.

For verification and updates, see the [installation guide](plugins/ai-code-workflow/docs/installation.md).
The Release and the preview marketplace branch are published separately;
availability of a Release does not mean the remote marketplace is deployed.

## Developer quick start

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
`--all` with `--plugin ai-code-workflow`. `--host` accepts `claude`, `codex`, `zcode` or
`all`; only declared hosts are built for each selected plugin.

A distribution contains a shared local marketplace named `ai-code-local`,
individual plugin packages and individual ZIPs. Each ZIP contains only its
plugin and a matching single-plugin marketplace. Unzip to a stable directory,
then register and install through the host's native plugin system. See the
plugin's [installation guide](plugins/ai-code-workflow/docs/installation.md).
See [three-host publishing](docs/publishing.md) for release check/prepare/verify,
repository marketplaces and the manual GitHub draft workflow. Real host
acceptance is required before preparing a stable release.

Schema 2 release bundles add `installers/ID-VERSION-HOST-plugin.zip`: one
plugin root with its complete native package and `artifact.json`, without a
marketplace. Download and submission ZIPs retain their separate purposes.
Each plugin has its own Release. Reviewed distribution plans select fixed
assets for Claude/ZCode and a pinned version directory for Codex; marketplace
deployment follows human Publish as a separate step. Preview/stable markets
target `codex/marketplace-preview` and `codex/marketplace`. Publication and market
deployment are recorded separately; native transport and upgrades remain unverified. Existing `dist/` and
`ai-code-local` entries stay available until the new transports pass acceptance.

Source checks and package integrity checks do not certify native loading or
model behavior. Host acceptance and its evidence belong to each plugin.

## Repository map

| Path | Purpose |
|---|---|
| `catalog.json` | Explicit list of registered plugin directories |
| `distribution.json` | Channel branches, market names and fixed transport choices; no duplicate plugin versions |
| `plugins/<id>/` | Self-contained plugin source, manifest, resources, adapters, tests and documentation |
| `tooling/plugin_tool.py` | Shared list, validate, build, package check, marketplace sync, release and local distribution plan/check commands |
| `tooling/` | Shared source validation, packaging and marketplace generation |
| `tests/` | Shared tooling tests and the unified test runner |
| `docs/plugin-authoring.md` | How to add a plugin and declare its supported hosts |
| `docs/publishing.md` | Three-host release inputs, artifacts, evidence and channel submission |
| `.github/workflows/release.yml` | Manually prepare artifacts and optionally create a GitHub draft |
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

CodeVow's policy resolution, task records and receipted file staging
remain at `plugins/ai-code-workflow/scripts/workflow_tool.py` in the source and
`tools/workflow_tool.py` in its package. These are workflow-specific tools.

## License and provenance

MIT — see [LICENSE](LICENSE) and [NOTICE](NOTICE). The repository's early history
derives from Affaan Mustafa's ai-code. CodeVow's migration history and
preserved backend-engineering-lite license are documented in its
[README](plugins/ai-code-workflow/README.md) and
[migration guide](plugins/ai-code-workflow/docs/migration.md).
