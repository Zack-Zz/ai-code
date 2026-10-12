# Agent Delegation

[English](README.md) | 简体中文

将任务交给独立的 Claude Code、Codex 或 ZCode 会话，并把改动和结果带回当前
会话。适合希望另一位编码助手实现功能、检查代码或继续处理已有任务的场景。
插件 ID 为 `ai-agent-delegation`。

## 安装与准备

按[安装指南](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.zh-CN.md)在宿主中安装并启用插件，
可安装插件以市场列表为准。

需要 Python 3，以及单独配置的 `agent-bridge/v1` CLI。Agent Bridge 负责连接
编码助手和保存任务，需要 Node.js 22.16+；目标编码工具另行安装并完成原生认证。
按 [Bridge 入门与配置](https://github.com/Zack-Zz/ai-mcp/blob/main/packages/agent-bridge/README.md#构建与受控配置)
登记项目、工具和发起会话。

插件客户端从宿主运行环境读取以下设置：

| 设置 | 用途 |
|---|---|
| `AGENT_BRIDGE_BIN` | `agent-bridge` 不在 `PATH` 时，指定单个可执行文件路径 |
| `AGENT_BRIDGE_CONFIG` | 私有 Bridge 配置文件路径 |
| `AGENT_BRIDGE_CALLER_REF` | 已登记并绑定发起会话的调用者身份 |

使用配置中已有的调用者引用。插件不会安装 Bridge、登记身份或修改宿主全局设置。

## 使用示例

开启新会话，说明目标工具、任务和允许修改的范围：

- “交给 Claude Code 实现这个功能，只修改登录模块，并运行相关测试。”
- “交给 ZCode 审查这次改动，只读检查，不修改文件。”
- “让另一个 Codex 独立会话修复这个问题，完成后把结果带回来。”

助手会检查目标工具是否可用，整理交接信息，启动任务，并带回任务状态、
修改文件和验证结果。后续可以要求继续同一个任务并给出补充说明，或取消它。

指定工具不可用时会说明原因，由你决定是否换工具。普通开发和原生子代理
仍按原来的方式工作。派发只授权你明确要求的工作；提交、推送、打标签、合并、
创建 PR、安装、发布和向他人发消息分别需要另行授权。任务记录和回执不会产生授权。

## 更多帮助与许可证

- [安装、更新和卸载](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.zh-CN.md)
- [Agent Bridge 入门](https://github.com/Zack-Zz/ai-mcp/blob/main/packages/agent-bridge/README.md#构建与受控配置)
- 高级资料：[派发技能](skills/agent-delegation/SKILL.md)、[Bridge 客户端命令](skills/agent-delegation/references/bridge-client.md)与[交接契约](skills/agent-delegation/references/handoff-contract.md)

[MIT](LICENSE)，维护者 Zack-Zz。
