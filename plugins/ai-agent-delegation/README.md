# Agent Delegation

English | [简体中文](README.zh-CN.md)

Hand a task to an independent Claude Code, Codex or ZCode session and bring its
changes and results back to your current conversation. Use it when you want
another coding assistant to implement a feature, review code or continue an
existing task. The plugin ID is `ai-agent-delegation`.

## Install and prepare

Follow the [installation guide](../../docs/installation.md) to install and enable the
plugin in your host. Available plugins are listed in the marketplace.

You need Python 3 and a separately configured `agent-bridge/v1` CLI.
Agent Bridge connects the coding assistants and keeps task state; it requires
Node.js 22.16+ and separately installed, authenticated target tools.
Follow [Bridge setup and configuration](https://github.com/Zack-Zz/ai-mcp/blob/main/packages/agent-bridge/README.md#构建与受控配置)
to register the project, tools and caller session.

The plugin's client uses these settings from the host's environment:

| Setting | Purpose |
|---|---|
| `AGENT_BRIDGE_BIN` | Single executable path when `agent-bridge` is outside `PATH` |
| `AGENT_BRIDGE_CONFIG` | Path to the private Bridge configuration |
| `AGENT_BRIDGE_CALLER_REF` | Existing registered caller identity bound to the originating session |

Use your configured caller reference. The plugin does not install Bridge,
register identities or change your host's global settings.

## Usage

Start a new session and name the target tool, task and permitted scope:

- “Ask Claude Code to implement this feature. Only change the login module and run its tests.”
- “Ask ZCode to review this diff without editing files.”
- “Have another independent Codex session fix this problem and bring back the results.”

The assistant checks the selected tool, prepares the handoff, starts the task,
and returns its status, changed files and verification results. You can ask it
to continue the same task with a follow-up, or cancel it.

If the selected tool is unavailable, the assistant explains why and lets you
choose an alternative. Ordinary development and native subagents keep their
usual behavior. A handoff covers the work you requested; commit, push, tag,
merge, PR creation, installation, publication and messages to others require
separate authorization. Task records and receipts do not grant it.

## More help and license

- [Installation, updates and uninstalling](../../docs/installation.md)
- [Agent Bridge setup](https://github.com/Zack-Zz/ai-mcp/blob/main/packages/agent-bridge/README.md#构建与受控配置)
- Advanced: [delegation skill](skills/agent-delegation/SKILL.md), [Bridge client commands](skills/agent-delegation/references/bridge-client.md) and [handoff contract](skills/agent-delegation/references/handoff-contract.md)

[MIT](LICENSE). Maintained by Zack-Zz.
