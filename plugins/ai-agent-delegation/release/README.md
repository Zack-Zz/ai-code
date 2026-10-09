# Agent Delegation

A candidate plugin for explicit user-directed handoff to an independent Claude Code,
ZCode or Codex session. One `agent-delegation` skill preserves the selected tool,
scope, task/session identity and result evidence. Tools are peers; there is no fixed
model routing or mandatory review pipeline.

Natural-language requests such as “交给 Claude Code 实现” and an explicit skill call
with a target are supported entry intentions. Ordinary work, native subagents,
discussion, quoted content and Agent-written approved flags do not dispatch.
Same-engine handoff requires an explicit independent-session request.

The plugin needs Python 3 and a separately installed/configured `agent-bridge/v1`
CLI. It includes a standard-library thin client, with no runtime, engine driver,
MCP server, automatic installer, credentials or task database. The host identifies
the actual current-user request and caller; the client does not authenticate a
human through NLP or an intent flag.

Read the [skill](skills/agent-delegation/SKILL.md),
[CLI contract](skills/agent-delegation/references/bridge-client.md),
[support matrix](docs/support-matrix.md), and [host evaluation plan](docs/host-evaluation.md).
Source validation, fixture tests and package integrity are separate from real host
acceptance. Claude Code, Codex and ZCode host behavior, natural-language loading,
engine execution, exact resumption and desktop visibility remain **unverified**.
No native MCP profile is shipped.

Publisher Zack-Zz is a public maintainer attribution, not platform certification.
Installation, Git actions and publishing require separate user authorization.
This candidate is not a stable accepted release. License: [MIT](LICENSE).
