# ai-code 文档导航

[English](README.md) | 简体中文

按阅读目的选择当前指南。带日期的设计与验证记录放在末尾的参考资料中。

## 使用插件

- [安装指南](installation.zh-CN.md)：各编码助手的市场安装、下载包安装、更新和卸载。
- [CodeVow](../plugins/ai-code-workflow/README.zh-CN.md)：功能、示例和配置。
- [CodeVow 详细用法](../plugins/ai-code-workflow/docs/usage.zh-CN.md)：配置、任务记录和可选文件工具。
- [Agent Delegation](../plugins/ai-agent-delegation/README.zh-CN.md)：依赖准备、派发、续接和取消。
- [CodeStack](../plugins/ai-code-stack-standards/README.zh-CN.md)：Java 写法与持久化易错点规则，当前为开发预览。
- [Agent Bridge 使用与配置](https://github.com/Zack-Zz/ai-mcp/blob/main/packages/agent-bridge/README.md#构建与受控配置)：外置运行时的准备入口。

## 开发插件

- [开发指南](../CONTRIBUTING.zh-CN.md)：环境、修改现有插件、测试、构建和本地试用。
- [插件作者指南](plugin-authoring.zh-CN.md)：新增插件的身份、资源、适配、注册和测试要求。
- [总体架构](architecture.zh-CN.md)：仓库结构、公共工具、插件及外置运行时的责任边界。

## 维护发行

- [发布指南](publishing.zh-CN.md)：发行准备、宿主验收、GitHub Release 和市场更新。
- [发行证据契约](release-evidence.zh-CN.md)：验收材料、公开摘要与 CI 的数据要求。

## 设计与历史资料

- [设计方案](design/)：按日期保存的规格与设计决定。
- [开发与验证记录](reviews/)：对应日期、源码和环境的检查记录。
- [CodeVow 设计](../plugins/ai-code-workflow/docs/design/)与[验证记录](../plugins/ai-code-workflow/docs/reviews/)：插件内部设计及测试背景。
- [迁移来源](../plugins/ai-code-workflow/docs/migration.md)与[历史资料](../plugins/ai-code-workflow/docs/bel-history/README.md)：来源、许可证和早期记录。

日常安装和开发使用上方当前指南。历史资料保留原日期和命令，仅用于追溯。
