# ai-code Maintainer Publishing Guide

English | [简体中文](publishing.zh-CN.md)

Prepare the version and notes locally, review and commit the source, then use
[Build & publish plugins / 构建与发布插件](../.github/workflows/release.yml)
in GitHub Actions. This is the single manual entry for building artifacts,
publishing a Release, and updating the stable marketplace. Installation is
covered by the [installation guide](installation.md); source development by the
[development guide](../CONTRIBUTING.md).

## Plugin version increments

These rules apply to every plugin in this repository:

- Start a new plugin at stable version `1.0.0`. Existing published `0.x` versions
  and historical records remain unchanged; continue their existing sequence
  unless the user explicitly specifies a target version or increment level.
- By default, advance exactly one patch version: `X.Y.Z → X.Y.(Z+1)`.
  For example, `1.0.5 → 1.0.6` and `0.1.0 → 0.1.1`.
- Use the plugin's latest published stable version as the baseline. Keep one
  candidate version for the same unreleased change; commits, reviews, fixes and
  repeated checks do not each trigger another increment.
- Continue the original plugin's version sequence when its ID or name changes.
  A rename, new host, new feature or incompatible change does not authorize the
  AI to choose a major/minor increment or skip version numbers.
- Depart from the default only when the user explicitly specifies a target
  version or increment level. Implementation, Git delivery and publication
  authorization do not imply permission to choose a larger increment.
- Keep preview releases opt-in. When the user requests another preview of the
  same target version without specifying a sequence, increase `preview.N` by one.
  Published versions and their history remain immutable.

This is the repository's version-selection convention. The local helper still
requires an explicit `--version`; the AI resolves that value before calling it.

## Prepare a version with AI

Ask, for example: “Help me prepare CodeVow 1.0.3: add local version preparation
and simplify publishing.” Give the plugin and changes; a target version is
optional and otherwise follows the patch rule above. The AI drafts the
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
python3 tooling/plugin_tool.py release prepare-version --plugin codevow --version 1.0.3 --notes-file /private/tmp/codevow-1.0.3-notes.md
python3 tooling/plugin_tool.py release prepare-version --plugin codevow --version 1.0.3 --notes-file /private/tmp/codevow-1.0.3-notes.md --apply
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
python3 tooling/plugin_tool.py release check --plugin codevow --mode draft
python3 tooling/plugin_tool.py release prepare --plugin codevow --mode draft --output /private/tmp/codevow-release
python3 tooling/plugin_tool.py release verify --plugin codevow --path /private/tmp/codevow-release
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
| `plugin` | `codevow`, `ai-agent-delegation`, `codestack` |
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

## DSH artifacts and identity replacement

The unreleased source IDs are `codevow` and `codestack`. Their current candidate
versions are 1.0.6 and 1.0.0. Existing public records keep their old identities
until a verified replacement release is synchronized. Do not edit `published/`
or marketplace manifests to simulate that transition.

A bundle containing DSH requires release schema 3 and package index schema 3.
Both source-bound and historical verification reject older schema declarations
for DSH; legacy release formats remain valid only for products without DSH.
Its native asset is
`installers/ID-VERSION-dsh-plugin.tgz`; its qualified download is
`downloads/ID-VERSION-dsh.tgz`. Other hosts keep ZIPs. The installer has the npm
`package/` prefix and no local index or install script. Native Git installation
uses the same files under `published/dsh/ID/VERSION/`. The public format-1 plugin
index lives at `published/dsh/index.json`, with a fixed commit, subdirectory,
actual Unix-seconds publish time and matching engines. Preview releases never
enter this index.

Distribution schema 3 records `git_installs` separately for Codex and DSH.
The first marketplace commit D contains exact installation files and a closed
`published/staged/ID/VERSION.json` receipt. Public checking verifies this pending
state against its frozen source and original plan; orphan directories are
rejected. Commit C binds the actual D, updates pointers and all native listings,
then consumes the staged receipt. Remote Release verification remains a distinct
check; an offline source check does not claim it has read remote assets.

`published/index.json` schema 3 separates active `plugins` and permanent
`retired` old-to-new mappings. A stable replacement retires only its own old ID
in the same successful update. Historical records, tags and installation bytes
are not rewritten. Lock schema 2 hashes four listing files and separately hashes
the published index. Legacy schema-2 records and schema-1 receipts are verified
without rewriting their bytes. Failed publication leaves old active entries
usable; a completed retirement is repaired with a higher version of the new ID.

Real DSH Web-profile loading, explicit/automatic skill invocation, reference
reading, Reviewer restrictions, long conversations and lifecycle still require
separate evidence. See the [migration guide](migrations/2026-10-27-plugin-identities.md).
