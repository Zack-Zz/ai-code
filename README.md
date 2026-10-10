# ai-code

English | [简体中文](README.zh-CN.md)

A repository for AI-related plugins. Each plugin owns its source, identity,
version, resources, tests and support claims. Shared tooling registers plugins,
validates their source, builds reproducible host packages, generates temporary
development marketplaces and verifies the public main snapshot. Plugin behavior
stays within its own directory.

The first plugin is **CodeVow — AI Coding Workflow** (`ai-code-workflow`),
an engineering workflow for AI coding assistants. More plugin types can be added when their
requirements are concrete; the repository does not impose workflow skills,
policies or task records on every plugin.

## Plugins

| Plugin | Purpose | Version and support |
|---|---|---|
| [CodeVow](plugins/ai-code-workflow/README.md) | Planning, TDD, debugging, review, verification and delivery evidence | Historical GitHub Prerelease `1.0.2`; no stable release; [real-host acceptance remains unverified](plugins/ai-code-workflow/docs/support-matrix.md) |
| [Agent Delegation](plugins/ai-agent-delegation/README.md) | Explicit handoff to another agent tool or an independent same-tool session through an external Agent Bridge | Source candidate `0.1.0`; [full host acceptance remains unverified](plugins/ai-agent-delegation/docs/support-matrix.md); no stable release; not included in the historical preview marketplace |

`catalog.json` registers plugin directories. Each directory's `product.json`
is the sole source of its plugin ID, version and resource whitelist. The root
private Node package is maintenance tooling; its version is not a plugin
release version.

See the [repository architecture](docs/architecture.md) and [documentation index](docs/README.md)
for module boundaries. Agent Delegation leaves ordinary development and native subagents
unchanged; its Bridge runtime and CLI/MCP/API live in the separate ai-mcp project.

## Install from the main marketplace after its first stable release

New distribution uses one marketplace on `Zack-Zz/ai-code` at `main`. Each
plugin ID has one current entry: its latest successfully synchronized stable
release. New `X.Y.Z-preview.N` versions are GitHub Prereleases only and do not
change that entry. The internal marketplace name remains `ai-code-preview`;
that name no longer describes its release kind.

**These CodeVow main installation examples become usable only after CodeVow's
first stable release has passed acceptance and synchronized successfully.** The migrated
root marketplace is an empty stable-only snapshot. Neither CodeVow nor Agent
Delegation currently has a stable entry; source registration is not publication.
The new main distribution path and version upgrades have not passed real-host
acceptance. The dated installation results below apply to the old preview path.

For Codex, register main and then install the available stable plugin:

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref main
codex plugin add ai-code-workflow@ai-code-preview
```

For a compatible Claude Code CLI, use the main JSON URL:

```sh
claude plugin marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/.claude-plugin/marketplace.json
claude plugin install ai-code-workflow@ai-code-preview
```

For the macOS ZCode bundled CLI, use its own main JSON URL:

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install ai-code-workflow@ai-code-preview
```

CLI versions and source-format constraints are recorded in the historical
section below. They do not establish acceptance of these new main URLs. Keep
the old marketplace registration until the main migration is explicitly
verified; the old preview branch remains a fixed historical trial source and
receives no new versions.

These are first-registration examples. Existing users need a separately
verified native source migration because the marketplace name is reused;
adding a URL does not prove that an existing registration changed source.

Updates have three separate states: refresh marketplace metadata, upgrade the
installed plugin through the host's native controls, then reload or start a new
session and verify the loaded version and package bytes. Publishing does not
upgrade a local installation. Two consecutive stable-version upgrades and
Codex's earlier refresh timeout still require live verification.

## Historical CodeVow 1.0.2 preview installation (2026-10-09)

[CodeVow 1.0.2](https://github.com/Zack-Zz/ai-code/releases/tag/ai-code-workflow%2Fv1.0.2)
and the [preview marketplace](https://github.com/Zack-Zz/ai-code/tree/codex/marketplace-preview)
are published. This is a prerelease. The host retrieves the plugin for you;
you do not need to download a ZIP, check out source or build it yourself.
Installation and full workflow acceptance are tracked separately in the
[native installation record](docs/reviews/2026-10-09-preview-marketplace-native-installation.md).

### Codex

Register the marketplace once, then install CodeVow:

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref codex/marketplace-preview
codex plugin add ai-code-workflow@ai-code-preview
```

These commands were verified with Codex CLI `0.154.0`: version `1.0.2` was
installed and enabled, and all 40 installed files matched the published plugin
package. Start a new host session to use it; workflow behavior remains pending.
Marketplace refresh attempts timed out, so updates are not yet verified.

### Claude Code

For Claude Code `2.1.292` or later, register and install in one command:

```sh
claude plugin install ai-code-workflow --marketplace \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/codex/marketplace-preview/.claude-plugin/marketplace.json
```

For `2.1.224`–`2.1.291`, register and install separately:

```sh
claude plugin marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/codex/marketplace-preview/.claude-plugin/marketplace.json
claude plugin install ai-code-workflow@ai-code-preview
```

The archive source requires `2.1.224` or later. See the official
[archive source reference](https://code.claude.com/docs/en/plugins/marketplace-reference#archive-plugin-source)
and [installation commands](https://code.claude.com/docs/en/discover-plugins#add-and-install-from-your-shell).
The single command was verified with the official `2.1.295` CLI: version `1.0.2`
was installed and enabled, all 35 files matched the published Claude package,
and a same-version marketplace refresh succeeded. Workflow behavior and version
upgrades remain pending. The native installation record also tracks the local
CLI launcher's update separately. The local default launcher is still `2.1.177`;
its update has not passed verification. Use an updated compatible CLI for the
commands above.

### ZCode

Register the ZCode JSON URL directly. Registering this multi-host Git repository
selects the Claude marketplace first on ZCode `3.14.5`.

The application's bundled native CLI was verified on macOS (`0.16.9`):

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/codex/marketplace-preview/marketplace.json
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install ai-code-workflow@ai-code-preview
```

Version `1.0.2` was installed and enabled, six skills were discovered, and all
35 installed files matched the ZCode Release package. Other installed plugins
were preserved. Start a new ZCode session; workflow behavior remains pending.

## Download historical CodeVow 1.0.2 as a fallback

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
The Release and the preview marketplace branch are published separately.
This version has both; full host acceptance and version upgrades remain pending.

## Developer quick start

Run from the repository root with Python 3.11+ and Node 22+:

```sh
python3 tooling/plugin_tool.py list
python3 tooling/plugin_tool.py validate --all
npm ci --no-audit --no-fund
npm test
python3 tooling/plugin_tool.py build --all --host all --output /tmp/ai-code-packages
python3 tooling/plugin_tool.py package check \
  --path /tmp/ai-code-packages/codex/ai-code-workflow --host codex --root .
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
Draft upload, verified publication and main marketplace synchronization. A new
stable release requires actual byte-bound host acceptance.

Development marketplaces stay in an explicit empty temporary directory:

```sh
python3 tooling/plugin_tool.py marketplace sync --output /tmp/ai-code-development
python3 tooling/plugin_tool.py marketplace check --root .
```

Register `/tmp/ai-code-development/<host>` only for an explicit development
trial. `marketplace check` reads the public snapshot and verifies its frozen
source S and pinned Codex distribution commit D; it does not require the public
version to match current development source. `dist/` is ignored temporary output
and must never be committed or pushed.

Schema 2 bundles include `installers/ID-VERSION-HOST-plugin.zip`, containing one
complete native plugin root and `artifact.json` without a marketplace. Downloads
and submission ZIPs keep their separate purposes. New preview versions stop at
GitHub Prerelease. Successful stable publication explicitly calls the reviewed
main marketplace workflow. Claude/ZCode use fixed Release assets; Codex uses
`published/codex/ID/VERSION/` pinned to an actual distribution commit. Source,
Release publication, market synchronization and real-host acceptance are
separate results. The new workflow code is local implementation, not evidence
of a successful remote run.

Source checks and package integrity checks do not certify native loading or
model behavior. Host acceptance and its evidence belong to each plugin.

## Repository map

| Path | Purpose |
|---|---|
| `catalog.json` | Explicit list of registered plugin directories |
| `distribution.json` | Main source, one marketplace identity, latest-stable policy and host transports |
| `plugins/<id>/` | Self-contained plugin source, manifest, resources, adapters, tests and documentation |
| `tooling/plugin_tool.py` | Shared list, validate, build, package check, development market sync, public market check/initialize, release and distribution plan/check |
| `tooling/` | Shared source validation, packaging and marketplace generation |
| `tests/` | Shared tooling tests and the unified test runner |
| `docs/plugin-authoring.md` | How to add a plugin and declare its supported hosts |
| `docs/publishing.md` | Three-host release inputs, artifacts, evidence and channel submission |
| `.github/workflows/release.yml` | Prepare frozen tagged source; review, upload and verify a Draft, then publish; stable success calls market sync |
| `.github/workflows/marketplace.yml` | Plan and review stable-only main synchronization, then deploy against the approved base |
| `docs/design/2026-10-07-multi-plugin-design.md` | Multi-plugin boundaries, contracts and migration plan |
| `published/` | Stable release records, current pointers, ownership receipt and pinned Codex installation content |
| `dist/` | Ignored, rebuildable local/CI output; never tracked |

## Development

- Read the root `AGENTS.md` and the plugin's local instructions before editing.
- Behavioral changes use meaningful RED then GREEN tests. Run `npm test` for
  the shared tooling and every registered plugin's test groups.
- Install locked maintenance dependencies with `npm ci`, then run `npm run lint`.
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
