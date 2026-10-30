# Reed interaction demo

English | [简体中文](README.zh-CN.md)

**Many agents. One flow.**

A frontend prototype of Reed, the local workflow workbench. It follows the confirmed native light design and balanced R identity, with system, light and dark appearance choices.

## Explore

- Personal board: To do, In progress, In review and Done; cards retain their workflow phase and links to documents, sessions and branches. Drag cards or use the Move menu. Task details open in a right drawer, preserving the board, filters and scroll position; document and session previews stay in context. Review and completion require valid outputs, workflow conditions and explicit confirmation of the exact version.
- Tasks: list and phase board, search, source and stage filters, create, import, pause, archive and restore.
- Workflow: requirements → design → development → verification, explicit acceptance, feedback, retries and rework with history retained.
- Documents: read, edit, retain versions and download Markdown. Rework and feedback mark old outputs as stale; submit a new version before reviewing them again.
- Associations: switch between task, session and branch perspectives; inspect related history and workspace context.
- Development preparation: choose a simulated host, prepare an isolated workspace, verify the session directory and then start.
- Connectors: configure multiple named Yunxiao connections using the official CLI integration model, with central or Region editions. Walk through identity, staged checks, project/type scope and status mapping; disable connections without deleting their history. Every entity retains its own origin.
- Sync: simulate pending changes, competing remote edits, conflict resolution and unknown outcomes that require reconciliation.

Start with **REQ-1042 → 确认设计** to explore development preparation. Use **我的看板** for progress across phases; the task board remains grouped by phase. All four host choices and external results are explicitly simulated.

## Configure a demo source

Open **连接器** at the bottom of the sidebar (the plug button in a narrow window). A catalog opens over the current task or board. Under Yunxiao, choose **自定义配置** for manual setup or **发现本机配置** to discover local mock candidates. **已添加的连接** opens an existing connection for editing; **管理全部** explicitly opens the full management page.

Discovery provides central, Region and incomplete examples. Each candidate generates an editable, read-only default draft; it is added only after explicit saving. Matching identities open existing connections. Missing organization IDs must be supplied. Empty results and unavailable local service scenarios retain retry and manual setup paths. No environment, files, CLI or real credentials are inspected. The saved connection retains only a small description of its configuration source.

Both setup paths continue through four steps:

1. **连接身份**: name the connection and choose central or Region edition. Central requires an organization ID; Region requires an HTTPS instance address. Choose a simulated account, PAT permission scenario and CLI availability. There is no real Token field.
2. **连接检测**: simulate CLI/plugin availability, PAT validation, instance/organization identity and project reads. Failed prerequisites stop later checks; save an unresolved configuration or go back and correct it.
3. **同步范围**: select simulated projects, a work item type and read-only or bidirectional sync.
4. **状态映射**: map Reed progress columns to remote status IDs per project/type. Apply suggestions, edit them and check the complete configuration before saving. Bidirectional configurations require complete mappings with compatible completion states. A read-capable connection without write permission stays readable, with pushing disabled.

Use **检测连接** to repeat all checks and inspect individual results. Expired PATs, missing CLI and denied project access are explicit local scenarios. Mapping or permission changes invalidate the corresponding checks. Real integration would use the local service and system credential store; this frontend never executes a CLI or contacts Yunxiao.

Import from an exact connection and project; deduplication uses connection, project and external ID. The source dialog shows edition, account, project, recorded work item type, Connector ID and external ID. The same external ID from different connections creates separate tasks. Renaming or disabling a connection preserves identity and existing data. Early caches retain legacy/unknown origins.

The sync dialog previews the mapped remote status and records its ID in a simulated read-back snapshot. This does not accept local workflow stages. Removing a project or changing the selected work item type blocks sync for excluded tasks while retaining their source and local work.

All single-select controls share the Reed menu style in light, dark and system appearance. Long lists support search, source grouping, official Yunxiao marks and connection descriptions. Use ↑/↓ to navigate, Enter to choose, Esc to close and Tab to continue; closing a menu inside a dialog keeps that dialog open. The official mark and its source are recorded in [asset provenance](public/assets/yunxiao-mark-source.txt).

## Personal settings

Open **Settings** at the lower left (the gear icon in compact navigation). Choose System, Light or Dark appearance and 简体中文 or English. Preferences stay in this browser. Language switching updates interface text, including menus and dialogs, while keeping task content, document bodies, connection names and remote state values in their original language. Filters and saved form drafts remain available. **Settings → About Reed** contains the demo explanation, export and reset; there is no separate Interaction preview sidebar entry.

## Local data and boundaries

This demo treats tasks in the local personal workbench as the personal collection; real team ownership and assignee filtering are not connected. Task state and appearance are stored in this browser's local storage; form drafts use session storage. Browser data clearing removes them. This is not yet the planned SQLite service, credential store or backup system. The About dialog exports a JSON snapshot and can reset only this demo's data.

No real Yunxiao API, MCP server, Agent execution, native session navigation, Git branch or worktree operation is connected. The demo does not read local repositories, hold credentials or synchronize external systems. It is not registered in the plugin marketplace.

## Development

Use Node.js 22.12 or later. Install with `npm ci`; run with `npm run dev -- --port 4173 --strictPort`. The development server binds to `127.0.0.1` by default. Network access requires an explicit host override; the development server stays on this computer.

- `npm test`: workflow state, data integrity and loopback listener tests.
- `npm run build`: production frontend and the retained optional hosting scaffold.
- `npm run test:sites`: local scaffold tests after building; this does not publish anything.

The root repository gate does not discover this unregistered prototype; run its tests separately. React rendering is checked by the production build and browser walkthrough. Root ESLint checks the prototype's JavaScript modules; JSX is outside that configuration's coverage.

See [design QA](design-qa.md), [verification](verification.md) and the [interaction specification](../docs/design/2026-10-28-reed-interaction-design.md). Screenshot evidence is local and ignored by Git under `.evidence/`.
