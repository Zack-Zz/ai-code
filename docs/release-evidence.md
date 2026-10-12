# Release Acceptance Evidence Contract

English | [简体中文](release-evidence.zh-CN.md)

This maintainer guide describes the acceptance data format used by the current
release tools. Recorded status comes from actual host verification. Use accepted
only after real scenarios have completed and a maintainer has checked the
materials. For installation and usage, see the
[user guide](installation.md).

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

## Actual acceptance and CI

Check Claude Code's fixed archive URL/SHA256, ZCode's ZIP URL/SHA256/path, and the
installation directory in Codex's fixed distribution commit separately. Record
marketplace registration, discovery, initial installation, updates, actual loaded
contents, and rejection of incorrect hashes. State conclusions only for what was
actually verified.

Keep separate evidence for Release publication, marketplace deployment, and
runtime behavior. A plan hash, record file, GitHub prerelease, or accepted marker
does not authorize Git operations, Publish, or deployment.

For each host, separately verify the native manifest, marketplace discovery,
installation and loading, skill invocation, workflow authorization boundaries,
Reviewer behavior, and the availability of packaged tools. Record the level of
verification reached and unfinished items. Script tests cannot prove that a host
actually follows Markdown. Native loading alone cannot justify marking all
behavior as accepted. Each declared host needs its own actual record.

By default, local `release check/prepare/verify` still requires readable
acceptance JSON and original materials, checking actual bytes item by item. A
clean GitHub checkout uses the hash declaration reviewed by the maintainer and
frozen with the source. It does not select an acceptance mode automatically from
environment variables or missing files.

After completing acceptance for all hosts, run this in the local source tree
that retains the private files:

```bash
python3 tooling/plugin_tool.py release acceptance-export --plugin ai-code-workflow
```

The command reads all acceptance records and logs under the existing strict
rules. It rejects export if any host is pending, a file is missing, or a hash does
not match. Its output is fixed at the plugin's `release/acceptance-proof.json`.
It contains only identity, version, source hash, all host package hashes, exact
public input hashes, and canonical paths and SHA256 values for acceptance files
and logs. It contains no summary, logs, or acceptance JSON bodies. Export and CI
reading share a 1 MiB limit. If an existing summary would change, review it first
and then explicitly use `--replace`. Identical exports are idempotent.

After reviewing the summary, commit it together with the final public inputs and
create the canonical tag. Keep original materials in ignored `private/` paths
within the plugin. The summary does not contain the final commit SHA, avoiding a
self-reference between a file and its containing commit. Actions separately
confirms that the summary bytes equal the Git blob at the tagged HEAD, requires
clean source and a canonical tag, and recalculates all public input and package
hashes. Changes to source, documentation, configuration, or package bytes require
acceptance and export to run again; the old summary cannot be reused.

Actions Prepare, Draft, Publish, and marketplace planning/deployment explicitly
use `committed_acceptance`. To reproduce that mode locally, pass
`--committed-acceptance`. Ordinary local commands continue checking actual
private files. A summary present in the worktree or HEAD must not fall back to
local mode because it is damaged, deleted, uncommitted, or stale. Ordinary local
mode requires complete private materials. Public artifacts retain a digest of
private inputs without their bodies. Both modes produce identical complete
artifact bytes for the same frozen source.

This summary is a factual declaration committed by a maintainer after local
verification, not a signing service or platform certification. CI cannot prove
the authenticity of private sessions again. Do not handwrite a summary in place
of acceptance. Human approval in `plugin-release` and `plugin-marketplace`
continues to provide the respective publication authorization; no new remote
keys are introduced.

accepted in evidence JSON is a factual declaration. Tooling cannot independently
prove session authenticity, platform approval, or model effectiveness. An Agent
writing accepted does not authorize a tag, Release, submission, or Publish.
See the [publishing process](publishing.md).
