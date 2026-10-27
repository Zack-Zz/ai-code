# Plugin identity migration — 2026-10-27

English | [简体中文](2026-10-27-plugin-identities.zh-CN.md)

This source change is not a published migration yet. Wait for the new IDs to
appear in your host's refreshed `ai-code` marketplace before removing a working
installation.

| Previous ID | New ID | Candidate version | Display name |
| --- | --- | --- | --- |
| `ai-code-workflow` | `codevow` | 1.0.6 | CodeVow |
| `ai-code-stack-standards` | `codestack` | 1.0.0 | CodeStack |

1. Use your host's native plugin controls to uninstall the previous IDs.
2. Refresh the existing `ai-code` marketplace; its name and source do not change.
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
rewrite is provided. DeepSeek Harness is a new host and has no old DSH ID to remove.

See the [installation guide](../installation.md) and [publishing guide](../publishing.md).

Optional file-operation staging/receipt namespaces follow the product ID. Old
file plans are retained but must be regenerated with the new tool before apply;
they are not silently adopted by the replacement plugin.
