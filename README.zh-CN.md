# ai-code

[English](README.md) | 简体中文

ai-code 是一个 AI 编码插件项目，帮助你在 Claude Code、Codex 和 ZCode 中
规划任务、开发代码、审查改动，以及与其他编码助手协作。

项目把可复用的技能、规则和辅助工具组织成独立插件。你可以按需要选择插件，
也可以开发自己的插件。各插件独立维护功能和配置，共用安装包构建与分发工具。

## 项目内容

| 插件 | 用途 | 使用说明 |
|---|---|---|
| **CodeVow** | 规划改动、测试驱动开发、排查问题、审查代码与验证结果 | [CodeVow](plugins/ai-code-workflow/README.zh-CN.md) |
| **Agent Delegation** | 将任务交给独立的 Claude Code、Codex 或 ZCode 会话，并收回结果；需要 Agent Bridge | [Agent Delegation](plugins/ai-agent-delegation/README.zh-CN.md) |

| 目录或文件 | 内容 |
|---|---|
| `plugins/` | 插件源码、使用说明、配置、适配与测试 |
| `tooling/` | 通用校验、构建、包检查和分发工具 |
| `tests/` | 公共工具测试和插件测试汇总 |
| `docs/` | 安装、开发、维护及参考文档 |
| `catalog.json` | 注册的插件目录 |
| `published/` | 市场分发所需的正式记录与安装内容 |

## 安装与使用

通过 ai-code 插件市场安装，或从 GitHub Release 下载对应编码助手的安装包。
插件市场名为 `ai-code-preview`，来源是 `Zack-Zz/ai-code` 的 `main` 分支。
可安装插件以市场列表为准，当前市场暂无可安装插件。

- [安装指南](docs/installation.zh-CN.md)：Claude Code、Codex、ZCode 的市场安装、下载包安装、更新和卸载。
- [CodeVow 使用说明](plugins/ai-code-workflow/README.zh-CN.md)：任务示例、协作模式和项目配置。
- [Agent Delegation 使用说明](plugins/ai-agent-delegation/README.zh-CN.md)：依赖准备、任务派发、续接和取消。

安装后新建会话，告诉编码助手你要完成什么任务。

## 开发与贡献

从[开发指南](CONTRIBUTING.zh-CN.md)开始：准备环境、修改现有插件、运行测试、
构建安装包和在本地试用。

新增插件请继续阅读[插件作者指南](docs/plugin-authoring.zh-CN.md)。项目结构见
[总体架构](docs/architecture.zh-CN.md)，发行维护见[维护者发布指南](docs/publishing.zh-CN.md)。

## 常见问题与其他说明

**需要安装 Node.js 或 Python 吗？** CodeVow 的 Markdown 技能无需这两个运行时；
可选管理工具需要 Python 3.11+。Agent Delegation 需要 Python 3 和外置 Agent
Bridge。完整要求见各插件说明。源码开发环境见开发指南。

**两个插件必须一起使用吗？** 可以独立选择。CodeVow 组织当前编码工作，
Agent Delegation 负责你明确要求的独立会话任务。

**如何更新或报告问题？** 更新步骤见安装指南；问题和建议请提交到
[GitHub Issues](https://github.com/Zack-Zz/ai-code/issues)，注明所用插件、编码助手
及复现步骤。[文档导航](docs/README.zh-CN.md)汇总当前指南和参考资料。

## 许可证与来源

[MIT](LICENSE)，另见 [NOTICE](NOTICE)。仓库早期历史派生自 Affaan Mustafa
的 ai-code。CodeVow 演进自 backend-engineering-lite，其许可证保留在
[插件目录](plugins/ai-code-workflow/LICENSES/backend-engineering-lite.txt)。
