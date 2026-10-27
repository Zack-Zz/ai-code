# Release Acceptance Evidence Contract

English | [简体中文](release-evidence.zh-CN.md)

Technical publication and real host acceptance are separate results. A stable
Release and marketplace update may proceed with host slots still `null` or
pending. Script tests, package hashes, and successful publication do not establish
native installation, skill invocation, or runtime behavior. Use `accepted` only
after real scenarios have completed and a maintainer has checked their materials.
This guide preserves the optional strict evidence format and exporter. Ordinary
publication does not require maintainers to handwrite acceptance JSON. See the
[user guide](installation.md) and [publishing guide](publishing.md).

## Release configuration

Each plugin's `release.json` declares only paths and host slots:

```json
{
  "schema_version": 1,
  "notes": "release/NOTES.md",
  "readmes": {"en": "release/README.md", "zh-CN": "release/README_CN.md"},
  "acceptance": {"claude": null, "codex": null, "zcode": null}
}
```

acceptance must cover exactly the hosts in product.json. `null` means no
acceptance exists yet. When a record exists, specify a canonical relative path
within the plugin directory. Absolute paths, `..`, symbolic links, and reads
across plugins are rejected. Configuration and evidence JSON reject duplicate
and unknown fields. Documentation must be nonempty UTF-8 Markdown.

## Acceptance records

The fixed record fields are schema_version, status, host, version,
source_tree_hash, package_content_hash, host_version, summary, and artifacts.
For example, an unverified record:

```json
{
  "schema_version": 1,
  "status": "unverified",
  "host": "codex",
  "version": "1.0.0",
  "source_tree_hash": "REPLACE_WITH_CURRENT_SOURCE_SHA256",
  "package_content_hash": "REPLACE_WITH_CURRENT_CODEX_PACKAGE_SHA256",
  "host_version": null,
  "summary": "Real host acceptance has not been performed",
  "artifacts": []
}
```

This example only demonstrates the fields. Take the version from the target
plugin's product.json and use actual hashes; it cannot be used directly as a valid
record. Actual values come from source_tree_hash and
readiness.package_content_hashes in `release check --plugin ID --mode draft`.
Use the current value for the corresponding host. Do not substitute a ZIP hash or
the hash of artifact.json for package_content_hash.

An accepted record must include nonempty host_version, summary, and artifacts.
Each artifact is
`{"path":"private/acceptance/codex-session.txt","sha256":"actual 64-character lowercase SHA256"}`.
Record the model, platform version, test commands, native loading and behavior
results, verifier, and time in the session materials. summary briefly describes
the results and remaining limitations. Paths remain anchored to the plugin's
source directory, and the actual file content SHA256 must match. Every record's
host, version, source hash, and package hash must match the current candidate.
unverified must not claim a host_version or include acceptance artifacts.

Original material paths must not be public source inputs, release notes, or
configuration. Hard links or copies with identical bytes must not register
private materials as public inputs either. Release tooling writes only status,
path bindings, and hashes into machine records. It does not copy the bodies of
original materials or acceptance JSON into release artifacts. Humans must still
check the public allowlist and document contents; tooling does not identify
sensitive information in arbitrary text fragments.

## Independent host verification

Report source checks, package integrity, Release publication, marketplace
synchronization, and host runtime verification separately. A technically ready
stable report may have `publication_ready=true` and nonempty
`pending_acceptance` together. List `accepted_hosts`, pending hosts, and
`limitations` without turning pending into an acceptance pass.

Check Claude Code's fixed archive URL/SHA256, ZCode's ZIP URL/SHA256/path, and
Codex's installation directory at the fixed distribution commit separately.
Record marketplace registration, discovery, initial installation, updates,
actual loaded contents, and rejection of incorrect hashes. Then verify skill
invocation, authorization boundaries, Reviewer behavior where applicable, and
packaged tools. State only the level actually reached; native loading alone
does not establish every behavior. Each host claimed as accepted needs its own
actual record. Post-publication host results can remain independent verification
reports bound to the tested version and bytes; they do not require changing an
immutable Release or its frozen source.

Null slots require no private files. When an evidence path is supplied, ordinary
local `release check/prepare/verify` reads the actual JSON and original materials
and checks their bindings strictly. Invalid, stale, or missing configured evidence
is an error, not an acceptance pass. A clean CI checkout can explicitly use
`--committed-acceptance` to verify a reviewed public summary without private
bodies. Actions uses this mode. With no summary and no evidence references, hosts
remain pending and technical publication can proceed. The tools do not switch
modes from environment variables or silently ignore broken supplied records.

## Optional strict acceptance export

If all declared hosts have completed byte-bound acceptance, run in a local source
tree that retains the private records and logs:

```sh
python3 tooling/plugin_tool.py release acceptance-export --plugin codevow
```

The exporter reads and verifies every record and actual log. Any pending host,
missing file, or hash mismatch prevents export. It writes only the plugin's
`release/acceptance-proof.json`, containing identity, version, source hash, all
host package hashes, exact public input hashes, and canonical paths and SHA256
values for evidence and logs. It contains no summary, log, or acceptance JSON
bodies. Export and committed reading share a 1 MiB limit. Identical exports are
idempotent; changed existing summaries require review and explicit `--replace`.
Do not handwrite a summary to substitute for real tests.

Review the summary and freeze it with final public source in the canonical
`ID/vVERSION` tag as part of an authorized publication. Keep original materials
in ignored private paths inside the plugin. The summary omits its containing
commit SHA to avoid self-reference. Committed verification requires clean source,
the canonical tag, summary bytes equal to the HEAD Git blob, and recomputed public
input and package hashes. A present or HEAD-recorded summary cannot fall back to
private mode because it is corrupt, removed, uncommitted, or stale. Both modes
produce the same complete artifact bytes for the same frozen source.

Changed source, notes, configuration, or package bytes invalidate prior bindings.
To keep an acceptance claim, repeat the applicable host verification and export.
To prepare a new version without acceptance, the local `prepare-version` helper
can explicitly reset old evidence references and remove a recognized generated
summary, retaining private files and published history. Its preview lists those
changes. New hosts stay unverified; clearing a slot never establishes acceptance.

The summary is a maintainer's factual declaration, not platform certification,
a signature service, or proof that CI reran a private session. CI cannot establish
session authenticity or model effectiveness from hashes. Evidence JSON, an
Agent-written `accepted` marker, a plan hash, and the summary grant no permission
to commit, push, tag, publish, deploy, install, or submit to an official directory.
The authorized Actions publication still uses `plugin-release` and
`plugin-marketplace`; configured environment reviewers may pause the run. See the
[publishing process](publishing.md).

## DSH and renamed identities

The new products declare `claude`, `codex`, `zcode` and `dsh` acceptance slots.
Keep a DSH slot null until actual matching-version/profile evidence exists.
Record native bundle loading separately from TGZ integrity, invocation, lifecycle,
read-only Reviewer tool enforcement and workspace isolation. Guard unit tests do
not establish a real host restriction.

Renaming IDs and changing shared skill structure invalidate source/package hash
bindings. Keep old private material and immutable public history; use the version
preparation preview to reset stale references rather than relabel old evidence.
