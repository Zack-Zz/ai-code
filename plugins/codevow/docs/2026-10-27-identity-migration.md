English | [简体中文](2026-10-27-identity-migration.zh-CN.md)

# Plugin identity migration — 2026-10-27

The installation ID changes from `ai-code-workflow` to `codevow`. This source change does not
modify user installations. Uninstall the old plugin through the host's native
interface, refresh the same `ai-code` marketplace, install and enable the new ID,
and start a new session. Remove the old plugin first because both identities
provide the same skill names. First-time DSH installation has no old DSH identity
to remove. Availability follows published records; candidate source is not a
published release. Old Releases, tags and frozen files remain intact.

The project policy, tasks and evidence structures under `.ai-workflow/` stay the
same. File staging uses the new identity's `.ai-workflow/staged/codevow` and
`.ai-workflow/receipts/codevow.json`. Old staging, receipts and backups remain
untouched and are not adopted or migrated automatically. The new tool rejects
unapplied files plans generated for the old identity; regenerate them from the
new package rather than editing identities or paths in a plan. Restoring old
sessions requires separate host acceptance.
