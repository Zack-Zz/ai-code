# 安装 ai-code 插件

[English](installation.md) | 简体中文

通过 Claude Code、Codex 或 ZCode 安装已发布的插件。以下状态来自仓库当前的
[发行记录](../published/index.json)和三宿主市场清单，不代表已在线核验宿主列表：

| 插件 | ID | 用途 | 正式市场 |
|---|---|---|---|
| [CodeVow](../plugins/ai-code-workflow/README.zh-CN.md) | `ai-code-workflow` | 计划、TDD、排查、审查和验证 | 已登记：`1.0.4` |
| [Agent Delegation](../plugins/ai-agent-delegation/README.zh-CN.md) | `ai-agent-delegation` | 将任务交给独立编码助手会话 | 尚未发布 |
| [CodeStack](../plugins/ai-code-stack-standards/README.zh-CN.md) | `ai-code-stack-standards` | Java 写法与持久化规则 | 开发预览，未进入正式市场 |

当前可安装项和版本以市场列表为准。下面的命令用于安装 CodeVow。
Agent Delegation 与 CodeStack 已有源码，但正式市场尚未列出
`ai-agent-delegation@ai-code` 或 `ai-code-stack-standards@ai-code`；
本地开发包和试用方式见[开发指南](../CONTRIBUTING.zh-CN.md)。

## 从插件市场安装

来源为 `Zack-Zz/ai-code` 的 `main`，市场名称为 `ai-code`。
用户无需手动克隆源码仓库或构建安装包，编码助手会自行获取所登记的来源。
注册一次后，再安装市场列表中已有的插件。

下面的 `sh` 命令块在系统终端执行，不是在编码助手的交互会话中输入。
每条命令成功后再执行下一条。如果已使用正确来源注册 `ai-code`，跳过添加
市场的命令，从刷新市场、安装插件开始。

三个宿主分别使用自己的市场清单和安装来源：

| 宿主 | 添加方式 | 本仓库中的清单 | 插件安装来源 |
|---|---|---|---|
| Codex | `main` 分支的 GitHub 仓库 | `.agents/plugins/marketplace.json` | `git-subdir` |
| Claude Code | 清单的完整 URL，或 `main` 分支的 GitHub 仓库 | `.claude-plugin/marketplace.json` | `archive` |
| ZCode | 清单的完整 URL | `marketplace.json` | `url`，`type: zip` |

### Codex

使用支持原生插件市场的 Codex 版本。注册 GitHub 来源、刷新列表，再安装 CodeVow，
其中 `owner/repo` 是客户端支持的 GitHub 仓库简写：

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref main
codex plugin marketplace upgrade ai-code
codex plugin add ai-code-workflow@ai-code
```

检查插件状态：

```sh
codex plugin list --marketplace ai-code
```

Codex 读取 `.agents/plugins/marketplace.json`。也可以在桌面客户端的插件目录
选择 `ai-code`，选择 CodeVow 并安装、启用。安装后开启新会话。

### Claude Code

使用 **Claude Code 2.1.224 或以上版本**。本市场使用 `archive` 插件来源，
根据 [Claude Code 官方市场参考](https://code.claude.com/docs/en/plugins/marketplace-reference#plugin-sources)，
这种来源要求该最低版本。安装前执行 `claude --version` 核对版本。

添加 Claude 专用清单的完整 URL、刷新列表，再为本机当前用户安装 CodeVow：

```sh
claude plugin marketplace add https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/.claude-plugin/marketplace.json
claude plugin marketplace update ai-code
claude plugin install ai-code-workflow@ai-code --scope user
claude plugin list
```

也可以用 GitHub 简写替代上面的 URL 添加方式；
Claude Code 会读取 `.claude-plugin/marketplace.json`：

```sh
claude plugin marketplace add "Zack-Zz/ai-code#main"
```

两种添加方式任选其一；GitHub 命令只替换上面安装命令块的第一条命令。
安装后重启 Claude Code，或在**已打开的 Claude Code 会话内**执行：

```text
/reload-plugins
```

可在 `/plugin` 的 Installed（已安装）页检查并启用 CodeVow。
安装范围与加载方式见[官方命令行安装指南](https://code.claude.com/docs/en/discover-plugins#install-from-your-shell)。

如果版本已满足要求，交互式插件面板仍提示不支持该来源，在系统终端执行上面
的刷新市场、安装插件命令，然后重启会话。不能仅凭这条错误判断 CLI 版本过低。

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

选择 `ai-code`，选择 CodeVow 并安装、启用。也可以在 **macOS 且 ZCode 安装于
`/Applications/ZCode.app`** 时，用应用自带 CLI 注册来源、刷新列表、安装并启用 CodeVow：

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace update ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install ai-code-workflow@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins enable ai-code-workflow@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins list
```

该示例要求 `node` 已在 `PATH` 中。如果应用安装于其他位置，调整应用路径。
其他平台使用上面的桌面端步骤。

任一宿主安装后，都开启新会话。账号和所选模型仍由宿主管理。

## 下载包安装

打开 [GitHub Releases](https://github.com/Zack-Zz/ai-code/releases)，选择已发布
插件的 Release，再选择宿主文件：`claude`、`codex` 或 `zcode`。
仓库发行记录登记的是 CodeVow `1.0.4`；只下载目标插件实际存在的公开 Release，
在该 Release 页面核对版本与附件。

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

刷新市场用于获取最新目录。在系统终端更新已安装插件时，使用对应宿主的命令。

Claude Code：

```sh
claude plugin marketplace update ai-code
claude plugin update ai-code-workflow@ai-code --scope user
```

macOS 上的 ZCode：

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace update ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins update ai-code-workflow@ai-code
```

Codex 执行 `codex plugin marketplace upgrade ai-code` 后，在原生插件管理中检查
已安装版本。任一宿主更新后，重新加载或开启新会话。本地下载方式使用新包
作为注册来源。

卸载时，在宿主原生插件管理中禁用并移除插件。不再使用该市场的插件时，再
单独移除市场来源。卸载插件不会删除项目记录，也不会卸载单独安装的 Agent Bridge。

## 依赖要求

| 插件或功能 | 要求 |
|---|---|
| 每个插件 | 支持原生插件的宿主、宿主账号和所选模型 |
| Claude Code 正式市场安装 | 支持 `archive` 来源的 Claude Code **2.1.224+** |
| CodeVow Markdown 技能 | 无需额外 Node.js 或 Python |
| CodeStack 指令 | 无需额外运行时，也不依赖其他 ai-code 插件 |
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
- [CodeStack 范围与预览状态](../plugins/ai-code-stack-standards/README.zh-CN.md)
