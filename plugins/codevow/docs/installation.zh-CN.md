# 安装 CodeVow

[English](installation.md) | 简体中文

市场安装、Release 下载、更新、卸载和依赖要求见统一[安装指南](../../../docs/installation.zh-CN.md)。

按宿主选择：[Codex 桌面端与 CLI](../../../docs/installation.zh-CN.md#codex)、
[Claude Code 桌面端与 CLI](../../../docs/installation.zh-CN.md#claude-code)、
[ZCode 桌面端与 macOS 应用内置 CLI](../../../docs/installation.zh-CN.md#zcode)，或
[DeepSeek Harness 桌面端与独立 npm CLI](../../../docs/installation.zh-CN.md#deepseek-harness)。

CodeVow `codevow` 1.0.6 已发布，其 DSH 安装包和公开索引仍将 `engines.dsh`
与 DSH peers 精确锁定为 `0.2.1-rc.2`。本地 1.0.7 候选将二者声明为最低
`>=0.2.1-rc.2`，RC3 及更高版本可通过版本门槛，但候选尚未进入公开索引或 Release。
范围匹配不代表未来 API 已验证，真实桌面端验收仍为 pending。
桌面端自带 Node.js 与 pnpm，无需另行安装 npm CLI。

配置、任务记录和可选项目文件暂存见[使用 CodeVow](usage.zh-CN.md)。
