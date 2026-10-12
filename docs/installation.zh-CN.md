# 安装 ai-code 插件

[English](installation.md) | 简体中文

通过 Claude Code、Codex 或 ZCode 安装已发布的插件。
截至 **2026-10-12**，正式市场的可安装情况如下：

| 插件 | ID | 用途 | 正式市场 |
|---|---|---|---|
| [CodeVow](../plugins/ai-code-workflow/README.zh-CN.md) | `ai-code-workflow` | 计划、TDD、排查、审查和验证 | 可安装：`1.0.3` |
| [Agent Delegation](../plugins/ai-agent-delegation/README.zh-CN.md) | `ai-agent-delegation` | 将任务交给独立编码助手会话 | 尚未发布 |

当前可安装项和版本以市场列表为准。下面的命令用于安装 CodeVow。
Agent Delegation 已有源码，但目前无法通过 `ai-agent-delegation@ai-code` 安装；
本地开发和试用见[开发指南](../CONTRIBUTING.zh-CN.md)。

## 从插件市场安装

来源为 `Zack-Zz/ai-code` 的 `main`，市场名称为 `ai-code`。
用户无需手动克隆源码仓库或构建安装包，编码助手会自行获取所登记的来源。
注册一次后，再安装市场列表中已有的插件。

三个宿主分别使用自己的市场清单和安装来源：

| 宿主 | 添加方式 | 本仓库中的清单 | 插件安装来源 |
|---|---|---|---|
| Codex | `main` 分支的 GitHub 仓库 | `.agents/plugins/marketplace.json` | `git-subdir` |
| Claude Code | 清单的完整 URL，或 `main` 分支的 GitHub 仓库 | `.claude-plugin/marketplace.json` | `archive` |
| ZCode | 清单的完整 URL | `marketplace.json` | `url`，`type: zip` |

### Codex

使用支持原生插件市场的 Codex 版本。注册 GitHub 来源，
其中 `owner/repo` 是客户端支持的 GitHub 仓库简写：

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref main
```

Codex 读取 `.agents/plugins/marketplace.json`。
在桌面客户端的插件目录选择 `ai-code`，选择 CodeVow 并安装、启用。
CLI 安装命令为：

```sh
codex plugin add ai-code-workflow@ai-code
```

### Claude Code

使用 **Claude Code 2.1.224 或以上版本**。本市场使用 `archive` 插件来源，
根据 [Claude Code 官方市场参考](https://code.claude.com/docs/en/plugins/marketplace-reference#plugin-sources)，
这种来源要求该最低版本。安装前执行 `claude --version` 核对版本。

添加 Claude 专用清单的完整 URL，再安装 CodeVow：

```sh
claude plugin marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/.claude-plugin/marketplace.json
claude plugin install ai-code-workflow@ai-code
```

也可以用 GitHub 简写替代上面的 URL 添加方式；
Claude Code 会读取 `.claude-plugin/marketplace.json`：

```sh
claude plugin marketplace add "Zack-Zz/ai-code#main"
```

为 `ai-code` 市场选择其中一种添加方式，再通过原生插件管理安装、启用 CodeVow。

### ZCode

在 ZCode 桌面端先打开工作区，再进入 **设置 → 插件 → 创建 → 添加插件市场**，
填写以下清单的完整 URL：

```text
https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json
```

本仓库应使用这个完整 URL。ZCode 的 Git 导入在只填写 `Zack-Zz/ai-code` 时，
可能优先选择 `.claude-plugin/marketplace.json`，再考虑根目录清单。
Claude 清单中的 `archive` 安装来源不受 ZCode 安装器支持；
根目录清单使用 ZCode 的 `url`、`type: zip` 安装来源。

如果已添加仓库并出现
`Plugin source is invalid or unsupported for ai-code-workflow@ai-code: archive`，
在“市场源”面板移除该 `ai-code` 来源，重新添加上面的完整 URL，
刷新市场后再打开插件详情或安装。

选择 `ai-code`，选择 CodeVow 并安装、启用。macOS 自带 CLI 可使用：

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install ai-code-workflow@ai-code
```

任一宿主安装后，都开启新会话。账号和所选模型仍由宿主管理。

## 下载包安装

打开 [GitHub Releases](https://github.com/Zack-Zz/ai-code/releases)，选择已发布
插件的 Release，再选择宿主文件：`claude`、`codex` 或 `zcode`。
CodeVow 已有正式版 `1.0.3` Release；只下载目标插件实际存在的公开 Release，
版本以该 Release 显示的版本为准。

| 下载文件 | 适用方式 |
|---|---|
| `<ID>-<VERSION>-<HOST>.zip` | 手动本地市场安装，包含插件和市场文件 |
| `<ID>-<VERSION>-<HOST>-plugin.zip` | 市场分发使用的纯插件包，不包含本地市场 |

Release 套件中，本地市场包位于 `downloads/`，纯插件包位于 `installers/`。
手动安装选择第一种格式，同时下载 `SHA256SUMS`，核对下载包与对应
`downloads/` 条目的 SHA256，再解压到稳定目录。注册包含市场文件的解压根
目录，不是内部的插件目录：

| 宿主 | 解压根目录中的市场文件 | 注册方式 |
|---|---|---|
| Claude Code | `.claude-plugin/marketplace.json` | `claude plugin marketplace add /path/to/extracted` |
| Codex | `.agents/plugins/marketplace.json` | `codex plugin marketplace add /path/to/extracted` |
| ZCode | `marketplace.json` | 在原生市场界面添加该文件 |

选择注册后的来源，再安装插件。本地下载包使用 `ai-code-local`，实际名称以
解压后的市场文件为准。例如：

```sh
claude plugin install ai-code-workflow@ai-code-local
codex plugin add ai-code-workflow@ai-code-local
```

`-plugin.zip` 用于市场分发，手动本地安装使用带市场的下载包。保留已注册
本地市场的解压目录。

## 更新与卸载

更新时，在宿主原生市场管理中刷新来源、更新已安装插件，再重新加载或开启新
会话。本地下载方式使用新包作为注册来源。

卸载时，在宿主原生插件管理中禁用并移除插件。不再使用该市场的插件时，再
单独移除市场来源。卸载插件不会删除项目记录，也不会卸载单独安装的 Agent Bridge。

## 依赖要求

| 插件或功能 | 要求 |
|---|---|
| 两个插件 | 支持原生插件的宿主、宿主账号和所选模型 |
| Claude Code 正式市场安装 | 支持 `archive` 来源的 Claude Code **2.1.224+** |
| CodeVow Markdown 技能 | 无需额外 Node.js 或 Python |
| CodeVow 可选工具 | Python 3.11+；文件暂存需要支持 POSIX 文件操作的平台 |
| Agent Delegation | Python 3，以及单独配置的 `agent-bridge/v1` CLI |
| Agent Bridge | Node.js 22.16+；目标编码工具另行安装并完成原生认证 |

Agent Delegation 使用前，请按
[Agent Bridge 入门与配置](https://github.com/Zack-Zz/ai-mcp/blob/main/packages/agent-bridge/README.md#构建与受控配置)
登记项目、目标工具和发起会话。可执行文件不在 `PATH` 时设置
`AGENT_BRIDGE_BIN`；配置和调用者使用 `AGENT_BRIDGE_CONFIG`、
`AGENT_BRIDGE_CALLER_REF`。使用 Bridge 支持的平台，本插件不提供 Windows
原生执行入口。

安装插件不会自动安装依赖。

## 接下来

- [CodeVow 使用与配置](../plugins/ai-code-workflow/docs/usage.zh-CN.md)
- [Agent Delegation 使用示例](../plugins/ai-agent-delegation/README.zh-CN.md)
