# ai-code Maintainer Publishing Guide

English | [简体中文](publishing.zh-CN.md)

Prepare the version and notes locally, review and commit the source, then use
[Build & publish plugins / 构建与发布插件](../.github/workflows/release.yml)
in GitHub Actions. This is the single manual entry for building artifacts,
publishing a Release, and updating the stable marketplace. Installation is
covered by the [installation guide](installation.md); source development by the
[development guide](../CONTRIBUTING.md).

## Prepare a version with AI

Ask, for example: “Help me prepare CodeVow 1.0.3: add local version preparation
and simplify publishing.” Give the target version and changes. The AI drafts the
English and Chinese notes and prepares the source diff for review.

Use the repository skill
[$ai-code-plugin-release](../.agents/skills/ai-code-plugin-release/SKILL.md)
to apply this flow, for example: “Use $ai-code-plugin-release to prepare CodeVow
1.0.3; review the changes before any authorized Git delivery.”

The local helper reads a nonempty UTF-8 Markdown body with `### English` and
`### 中文` sections, without a version heading. For example, the AI can write
`/private/tmp/codevow-1.0.3-notes.md` containing:

```markdown
### English

- Add local version preparation and simplify publishing.

### 中文

- 增加本地版本准备命令，简化发布流程。
```

From the repository root, preview first, then apply the local edits:

```sh
python3 tooling/plugin_tool.py release prepare-version --plugin ai-code-workflow --version 1.0.3 --notes-file /private/tmp/codevow-1.0.3-notes.md
python3 tooling/plugin_tool.py release prepare-version --plugin ai-code-workflow --version 1.0.3 --notes-file /private/tmp/codevow-1.0.3-notes.md --apply
```

The default command writes nothing. `--apply` updates only the selected plugin's
`product.json` version and the notes declared by `release.json`, inserting the
version section while preserving history. Identical existing sections are
idempotent; conflicting same-version notes and downgrades are rejected. If the
new bytes invalidate old host evidence, the plan lists acceptance slots to reset
and a recognized generated `release/acceptance-proof.json` to remove. Private
materials and published records are preserved. All changes include old/new bytes
and hashes; host acceptance remains `unverified`. Inputs must use safe paths
without symbolic links; on macOS use a physical path such as `/private/tmp`.

The helper does not commit, push, tag, build, publish, or install. Review the
source diff and verification report, then explicitly authorize commit and push
for this change before running Actions. The root private `package.json` and
adapter templates are not plugin version sources.

## Versions and local checks

`product.json` is the sole source for plugin identity, version, hosts, publisher,
and resource allowlist. `release.json` declares notes, bilingual readmes, and
optional host evidence paths without duplicating the version. Versions are
`X.Y.Z` or `X.Y.Z-preview.N`, with no leading zeros, other suffixes, or build
metadata. Preview numbers compare numerically. The tag `ID/vVERSION` and release
kind are derived automatically.

| Version | GitHub Release | Marketplace |
|---|---|---|
| `X.Y.Z-preview.N` | Public prerelease | No update |
| `X.Y.Z` | Public stable release | Automatically synchronize after publication |

Use Node.js 22+, Python 3.11+, and POSIX file operations. Local checks and artifact
preparation are available independently of Actions:

```sh
npm ci --no-audit --no-fund
python3 tooling/plugin_tool.py validate --all
PYTHONDONTWRITEBYTECODE=1 npm test
npm run lint
python3 .github/scripts/check_no_dist.py --root .
python3 tooling/plugin_tool.py release check --plugin ai-code-workflow --mode draft
python3 tooling/plugin_tool.py release prepare --plugin ai-code-workflow --mode draft --output /private/tmp/codevow-release
python3 tooling/plugin_tool.py release verify --plugin ai-code-workflow --path /private/tmp/codevow-release
```

Output directories must be absent or empty. `verify` independently rebuilds the
resource and ZIP closure from trusted source. `--previous
/path/to/verified-bundle/release.json` checks version progression against a fully
verified reference bundle. Local preparation does not publish or install.

Stable technical readiness requires clean, frozen Git source, a canonical tag,
valid public inputs, and independently verified artifacts. Host acceptance is
reported separately through `pending_acceptance`, `accepted_hosts`, and
`limitations`; pending hosts do not block technical publication. Provided evidence
and summaries still undergo strict byte verification. See the
[release evidence contract](release-evidence.md).

## Run the single Actions entry

On GitHub Actions, select **Build & publish plugins / 构建与发布插件** and run it
on **main**. There are two inputs:

| Input | Choices |
|---|---|
| `plugin` | `ai-code-workflow`, `ai-agent-delegation` |
| `operation` | `build`, `publish` |

Version and notes come from the committed plugin source. There is no source-tag,
plan-hash, or evidence-path input.

- `build` runs checks, builds the complete release bundle, native installer ZIPs,
  download packages, and submission bundles, independently verifies them, and
  saves Actions artifacts. It performs no remote tag, Release, or marketplace
  writes.
- `publish` runs the same checks and build, creates or reuses the canonical tag,
  verifies the frozen source, uploads all Release attachments, reads their full
  bytes back, and publishes the version's release kind. For stable versions it
  automatically calls the internal reusable marketplace workflow; previews end
  at the public Release.

Publication uses `plugin-release`; marketplace deployment uses
`plugin-marketplace`. If these environments configure required reviewers, the
run pauses for their approval. A single workflow entry does not bypass those
approvals. The internal marketplace flow generates its plan and carries the plan
hash and main baseline into deployment; maintainers do not enter them manually.

## Artifacts, marketplace records, and retries

The schema 2 release bundle contains `packages/`,
`installers/ID-VERSION-HOST-plugin.zip`, `downloads/ID-VERSION-HOST.zip`,
`submissions/`, `release.json`, `SHA256SUMS`, and `release-notes.md`. Public Release
attachments include the complete `ID-VERSION-release-bundle.zip` with its checksum,
per-host download and native installer ZIPs, and release records. Submission
bundles do not imply inclusion in an official directory.

For a native single-plugin package, choose
`installers/ID-VERSION-HOST-plugin.zip`; it contains the plugin directory without
an extra local marketplace manifest. `downloads/ID-VERSION-HOST.zip` is the
development download with a local marketplace and `artifact.json`. Both outputs
are retained; public marketplace distribution uses the single-plugin installer.

`distribution.json` fixes main, the marketplace name `ai-code`, and the
latest-stable policy. Each plugin has one current stable entry. Claude Code and
ZCode use fixed Release attachments; Codex installation contents are pinned to
the actual distribution commit under `published/codex/ID/VERSION/`.
`published/index.json`, `published/releases/ID/VERSION.json`, and
`published/marketplaces.lock.json` retain the public records and ownership hashes.
The development version in `product.json` can differ from the published version.

Public manifests are generated, not edited manually. To check them read-only:

```sh
python3 tooling/plugin_tool.py marketplace check --root .
```

For an isolated development marketplace, use `marketplace sync --output
/private/tmp/ai-code-development` with an absent or empty directory. Its name is
`ai-code-local`. `dist/` stays ignored and out of commits; public ZIPs are Release
attachments.

Same-version tags, Release assets, and published records are immutable. Changed
public bytes require a new version, even if `product.json` was left unchanged.
A rerun can reuse a matching tag and Release only after complete verification.
If the Release is public but its marketplace update failed, report both states
and rerun `publish` for that same unchanged version to resume synchronization.
The previous usable marketplace entry remains until a verified update succeeds.
If publication itself is uncertain or uploads are incomplete, inspect the remote
state before retrying; never overwrite assets, move tags, or force push. A run is
complete only after its Release and, for stable versions, marketplace records
read back consistently. Host installation and runtime acceptance remain separate.
