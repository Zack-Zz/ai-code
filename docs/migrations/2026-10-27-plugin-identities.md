# Plugin identity migration — 2026-10-27

English | [简体中文](2026-10-27-plugin-identities.zh-CN.md)

CodeVow 1.0.6 and CodeStack 1.0.0 were published on 2026-10-27; the verified
market update activated their new IDs and retired the previous IDs. Refresh
your host's `ai-code` source and check version compatibility before removing
a working installation. See the [desktop and CLI procedures](../installation.md).

| Previous ID | New ID | Published version | Display name |
| --- | --- | --- | --- |
| `ai-code-workflow` | `codevow` | 1.0.6 | CodeVow |
| `ai-code-stack-standards` | `codestack` | 1.0.0 | CodeStack |

1. Refresh the existing `ai-code` marketplace and confirm the replacement is
   available and compatible; its name and source do not change.
2. Use your host's native plugin controls to uninstall installed previous IDs.
   If new versions are already installed, remove only the remaining old IDs.
3. Install and enable `codevow` and/or `codestack`, then start a new session.
4. Verify the expected version and skill catalog. Keep your project's `.ai-workflow/`
   policy, tasks and evidence; this migration does not rename that directory.

Only the plugins need reinstallation. The coding assistant itself is unchanged.
Old and new plugins share skill names, so remove the old installation first.
Skill names such as `workflow` and `code-standards` are unchanged. Existing-session
restoration is host-specific and is not claimed as a seamless migration.

Old Releases, tags, assets, fixed installation commits and historical records
remain immutable. The publisher retires each previous ID only in the same
verified marketplace update that activates its replacement. Failed publication
keeps the previous marketplace usable. No automatic uninstaller, alias or cache
rewrite is provided. DeepSeek Harness is a new host and has no old DSH ID to remove. The current
DSH bundles declare exactly `0.2.1-rc.2`; they do not cover `0.2.1-rc.3`, and
real Desktop/Web acceptance remains pending.

See the [installation guide](../installation.md) and [publishing guide](../publishing.md).

Optional file-operation staging/receipt namespaces follow the product ID. Old
file plans are retained but must be regenerated with the new tool before apply;
they are not silently adopted by the replacement plugin.
