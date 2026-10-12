# ai-code Maintainer Publishing Guide

English | [简体中文](publishing.zh-CN.md)

This guide describes the current release tools and workflows. For user
installation, see the [installation guide](installation.md); for source
development, see the [development guide](../CONTRIBUTING.md). Manage pre-release
checks and acceptance records in maintainer documents. The user README describes
only current features, installation, and usage.

## Release inputs and versions

A plugin's `product.json` is the sole source for identity, version, hosts,
attribution, and the public resource allowlist. `release.json` declares notes and
host acceptance paths without duplicating the version. The root Node package is
private maintenance tooling and is not published with npm publish.

Versions use only `X.Y.Z` or `X.Y.Z-preview.N`. Numbers must not have leading zeros;
other suffixes and build metadata are rejected. Tooling compares versions
numerically and rejects downgrades or different bytes for the same version.
The canonical source tag is `ID/vVERSION`.

| Version | Local mode | GitHub Prerelease | main marketplace |
|---|---|---|---|
| `X.Y.Z-preview.N` | draft | true | No update |
| `X.Y.Z` | stable | false | Synchronize after successful stable publication |

GitHub Draft means the release is not yet public and is separate from local
`mode=draft/stable`. The release kind is derived from the version. Git commits,
tags, public releases, and marketplace deployments each require explicit
authorization for the current change.

## Local checks and artifact preparation

Prepare Node.js 22+, Python 3.11+, and an environment that supports POSIX file
operations. Run commands from the repository root. Output directories must be
absent or empty; placing them outside the repository is recommended.

```sh
npm ci --no-audit --no-fund
python3 tooling/plugin_tool.py validate --all
PYTHONDONTWRITEBYTECODE=1 npm test
npm run lint
python3 .github/scripts/check_no_dist.py --root .
python3 tooling/plugin_tool.py release check --plugin ai-code-workflow --mode draft
python3 tooling/plugin_tool.py release prepare --plugin ai-code-workflow --mode draft --output /tmp/codevow-release
python3 tooling/plugin_tool.py release verify --plugin ai-code-workflow --path /tmp/codevow-release
```

`draft` is used for local preparation. `stable` requires clean Git, a canonical
tag, and byte-bound acceptance for all declared hosts. Review the report's
`publication_ready`, `pending_acceptance`, and `limitations`. Local commands do
not install plugins, upload artifacts, or modify Git.

`verify` independently rebuilds resources and the ZIP closure from trusted
source. To check version progression, use
`--previous /path/to/verified-bundle/release.json`. The reference bundle must
still pass complete byte verification; content cannot change for the same
version.

## Artifacts and the development marketplace

The current release manifest uses schema 2. Outputs serve these purposes:

| Artifact | Purpose |
|---|---|
| `packages/` | Host installation directories, plugin ZIPs, local marketplaces, and indexes |
| `installers/ID-VERSION-HOST-plugin.zip` | Complete single-plugin native package without a marketplace |
| `downloads/ID-VERSION-HOST.zip` | Manual download package with a local marketplace |
| `submissions/openai/ID-VERSION.zip` | skills-only submission package |
| `submissions/claude/`, `submissions/zcode/` | Channel source bundles and registration entries |
| `release.json`, `SHA256SUMS`, `release-notes.md` | Release record, file closure, checksums, and notes |

Generate development marketplaces only into explicit empty output directories:

```sh
python3 tooling/plugin_tool.py marketplace sync --output /tmp/ai-code-development
```

The marketplace name in each host directory is `ai-code-local`. See the
development guide for trial steps. `dist/` is ignored temporary output and must
not be committed. Public ZIPs are stored as Release attachments.

## main marketplace records

`distribution.json` maintains main, the marketplace name `ai-code-preview`, the
latest-stable policy, and host transport methods. Each plugin ID has only one
current stable entry.

| Path | Contents |
|---|---|
| `.agents/plugins/marketplace.json` | Codex entry point |
| `.claude-plugin/marketplace.json` | Claude Code entry point |
| `marketplace.json` | ZCode entry point |
| `published/index.json` | Synchronized stable versions and record references |
| `published/releases/ID/VERSION.json` | Immutable stable record and frozen source |
| `published/marketplaces.lock.json` | Managed manifests and hash receipts |
| `published/codex/ID/VERSION/` | Codex native installation contents |

Claude Code and ZCode use fixed Release attachments. The Codex entry fixes the
actual distribution commit. `product.json` maintains the development version;
`published/` maintains the marketplace version.

Public snapshot checking is read-only:

```sh
python3 tooling/plugin_tool.py marketplace check --root .
```

An empty marketplace does not substitute a preview for a stable entry. Do not
edit public manifests manually. Stable releases update them through the
marketplace planning and deployment process below.

## Host acceptance and the public summary

For each host declared by the plugin, perform real installation and task
scenarios, verify the version, loaded contents, authorization boundaries, and
results, then record evidence. See the
[release evidence contract](release-evidence.md) for the format.

After completing acceptance locally where private materials are readable, run:

```sh
python3 tooling/plugin_tool.py release acceptance-export --plugin ai-code-workflow
```

Tooling generates `release/acceptance-proof.json`, exporting only verified hash
declarations. After maintainer review, freeze the summary with the final public
source in the canonical tag, keeping original materials in private paths.
Actions explicitly uses committed acceptance and neither reads nor publishes
private bodies. The summary is a factual declaration; it grants no publication
authorization and does not replace real host tests.

## Prepare, Publish, and marketplace synchronization

[Release plugin](../.github/workflows/release.yml) accepts `plugin`, an existing
`source_tag`, and `operation=prepare|publish` through its manual entry on main.

1. Prepare uses trusted management tooling from main to read the frozen tag, verify its format and reachability from main, run tests and static checks, prepare artifacts, independently reverify them, and save an Actions artifact.
2. After approval in the `plugin-release` environment, Publish creates a Draft, uploads all attachments, reads each back and verifies the frozen tag, then publishes the corresponding release kind. It does not overwrite an existing Release of the same version or create tags.
3. After successful stable publication, explicitly invoke [Sync plugin marketplace](../.github/workflows/marketplace.yml). Previews stop at the Release.

Public inputs at the source tag must match Git blob bytes. Actions artifacts
preserve native hidden directories. Continue reading back the state after
publication. If it cannot be confirmed, report uncertain; do not automatically
retry or delete it.

Marketplace synchronization plan is read-only. deploy requires approval in the
`plugin-marketplace` environment, the hash of the actually reviewed plan, and the
main base SHA. Manual execution example:

```sh
python3 /path/to/trusted-main/.github/scripts/deploy_marketplace.py \
  --root /path/to/frozen-source --control-root /path/to/trusted-main \
  --plugin "$PLUGIN_ID" --source-tag "$SOURCE_TAG" --channel stable \
  --action plan --output /tmp/remote-market-plan.json
```

Review the Release, source, attachment hashes, path changes, and main baseline.
After authorization, deploy with the same inputs:

```sh
python3 /path/to/trusted-main/.github/scripts/deploy_marketplace.py \
  --root /path/to/frozen-source --control-root /path/to/trusted-main \
  --plugin "$PLUGIN_ID" --source-tag "$SOURCE_TAG" --channel stable \
  --action deploy --expected-plan-hash "$REVIEWED_HASH" \
  --expected-market-commit "$REVIEWED_MAIN_SHA" --output /tmp/deploy-result.json
```

These variables come from the selected plugin, its published stable tag, and the
actual review results; do not execute using placeholder values. The deployer
reverifies the Release, tag, all attachments, and stable gates. Codex installation
contents and marketplace records are committed in stages. Synchronization is
reported complete only when marketplace records read back consistently. Stop if
the base commit or bytes change. Use ordinary fast-forward updates, never force
push.

If the Release is public but the marketplace update fails, report both results
separately and preserve the current usable marketplace entry. Submission to an
official directory is a separate manual channel; generated submission bundles do
not mean official inclusion.
