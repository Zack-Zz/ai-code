English | [简体中文](2026-10-27-identity-migration.zh-CN.md)

# Plugin identity migration — 2026-10-27

The installation ID changes from `ai-code-stack-standards` to `codestack`. This source change does not
modify user installations. Uninstall the old plugin through the host's native
interface, refresh the same `ai-code` marketplace, install and enable the new ID,
and start a new session. Remove the old plugin first because both identities
provide the same skill names. First-time DSH installation has no old DSH identity
to remove. Availability follows published records; candidate source is not a
published release. Old Releases, tags and frozen files remain intact.
