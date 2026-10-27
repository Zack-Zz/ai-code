# 安装 ai-code 插件

[English](installation.md) | 简体中文

> 当前源码候选：CodeVow 使用 `codevow`（2.0.0），CodeStack 使用
> `codestack`（0.2.0），新增 `dsh` 适配。本次改动尚未发布，实际可安装版本仍由
> 冻结的 published 快照决定。以下新 ID 命令须在市场出现新入口后使用。
> 重新安装步骤见[身份迁移](migrations/2026-10-27-plugin-identities.zh-CN.md)。

通过 Claude Code、Codex 或 ZCode 安装已发布的插件。正式可用版本以仓库当前的
[发行记录](../published/index.json)和三宿主市场清单为准；安装前先刷新宿主中的列表。
CodeVow 与 CodeStack 共享同一个 `ai-code` 市场，各自独立：

| 插件 | ID | 用途 | 正式市场 |
|---|---|---|---|
| [CodeVow](../plugins/codevow/README.zh-CN.md) | `codevow` | 计划、TDD、排查、审查和验证 | 见当前发行记录 |
| [Agent Delegation](../plugins/ai-agent-delegation/README.zh-CN.md) | `ai-agent-delegation` | 将任务交给独立编码助手会话 | 尚未发布 |
| [CodeStack](../plugins/codestack/README.zh-CN.md) | `codestack` | 精选的 Java、数据访问和多语言前端约定 | 见当前发行记录 |

下面的命令用于安装 CodeVow。安装 CodeStack 时，将同一宿主安装命令中的插件
替换为 `codestack@ai-code`，或刷新市场后在界面中选择 CodeStack。
可以只安装其中一个，也可以同时安装。Agent Delegation 当前只有源码，尚未进入
正式市场。源码开发见[开发指南](../CONTRIBUTING.zh-CN.md)。

## 从插件市场安装

来源为 `Zack-Zz/ai-code` 的 `main`，市场名称为 `ai-code`。
用户无需手动克隆源码仓库或构建安装包，编码助手会自行获取所登记的来源。
注册一次后，再安装市场列表中已有的插件。

下面的 `sh` 命令块在系统终端执行，不是在编码助手的交互会话中输入。
每条命令成功后再执行下一条。如果已使用正确来源注册 `ai-code`，跳过添加
市场的命令，从刷新市场、安装插件开始。

声明宿主分别使用自己的市场清单和安装来源：

| 宿主 | 添加方式 | 本仓库中的清单 | 插件安装来源 |
|---|---|---|---|
| Codex | `main` 分支的 GitHub 仓库 | `.agents/plugins/marketplace.json` | `git-subdir` |
| Claude Code | 清单的完整 URL，或 `main` 分支的 GitHub 仓库 | `.claude-plugin/marketplace.json` | `archive` |
| ZCode | 清单的完整 URL | `marketplace.json` | `url`，`type: zip` |
| DeepSeek Harness | 显式原生插件索引 | `published/dsh/index.json` | 固定 Git bundle 或下载 TGZ |

### Codex

使用支持原生插件市场的 Codex 版本。注册 GitHub 来源、刷新列表，再安装 CodeVow，
其中 `owner/repo` 是客户端支持的 GitHub 仓库简写：

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref main
codex plugin marketplace upgrade ai-code
codex plugin add codevow@ai-code
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
claude plugin install codevow@ai-code --scope user
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
`Plugin source is invalid or unsupported for codevow@ai-code: archive`，
在“市场源”面板移除该 `ai-code` 来源，重新添加上面的完整 URL，
刷新市场后再打开插件详情或安装。

选择 `ai-code`，选择 CodeVow 并安装、启用。也可以在 **macOS 且 ZCode 安装于
`/Applications/ZCode.app`** 时，用应用自带 CLI 注册来源、刷新列表、安装并启用 CodeVow：

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace update ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install codevow@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins enable codevow@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins list
```

该示例要求 `node` 已在 `PATH` 中。如果应用安装于其他位置，调整应用路径。
其他平台使用上面的桌面端步骤。

任一宿主安装后，都开启新会话。账号和所选模型仍由宿主管理。

## DeepSeek Harness

`dsh` 适配面向标准 Web profile，声明 `engines.dsh` 为 `0.2.1-rc.2`；真实宿主
验收仍待完成。CodeVow 需要原生 Agent Preset 服务和 spawn 后端；首轮不声明
支持 minimal/SDK/ACP profile。安装依赖成功不等于插件激活成功。

本地试用请使用未占用的 profile 名称。首条命令创建 Web profile 并打印组合配置，
不要用它覆盖已有设置。下载匹配版本的 Release TGZ 后逐条执行：

```sh
dsh --profile ai-code-trial --from-default-profile web --dump-config
dsh plugin --profile ai-code-trial add ./codevow-2.0.0-dsh-plugin.tgz
dsh plugin --profile ai-code-trial add ./codestack-0.2.0-dsh-plugin.tgz
dsh --profile ai-code-trial --dump-config
dsh --profile ai-code-trial
```

源码试用可将 TGZ 参数替换为构建包的绝对目录，例如
`/private/tmp/ai-code-packages/dsh/codevow`。插件不提供安装时构建脚本。
在新会话使用 `/workflow` 或 `/code-standards`，引用资源随独立 bundle 保留。
CodeStack 不含自定义运行逻辑；CodeVow 使用原生 spawn Reviewer 和现有 Python 工具。

正式发布后，可以启用 Harness 可选的“自定义插件索引”组合包，并添加本仓库
`published/dsh/index.json` 的 raw HTTPS 地址。这是显式索引源，不是宿主自动扫描
的仓库清单。安装前核对 Harness 展示的固定 Git 提交和 bundle 子目录。
直接安装 TGZ/目录不需要该实验性发现功能；正式索引仅列稳定版本。

Git 安装使用正式索引生成的精确提交和子目录，不使用源码仓库根目录。
Git bundle 已含全部产物；升级按宿主卸载再安装的方式完成。
卸载使用 `dsh plugin --profile ai-code-trial remove codevow`（或 `codestack`），
不支持 HMR 的 profile 需要重启；无需自制安装器或修改宿主缓存。

## 下载包安装

打开 [GitHub Releases](https://github.com/Zack-Zz/ai-code/releases)，选择已发布
插件的 Release，再选择宿主文件：`claude`、`codex` 或 `zcode`。
以仓库当前发行记录为准；只下载目标插件实际存在的公开 Release，
在该 Release 页面核对版本与附件。

| 下载文件 | 适用方式 |
|---|---|
| `<ID>-<VERSION>-<HOST>.zip` | 手动本地市场安装，包含插件和市场文件 |
| `<ID>-<VERSION>-<HOST>-plugin.zip` | 市场分发使用的纯插件包，不包含本地市场 |

以下 ZIP 解压注册步骤适用于原三个宿主。DSH 使用上文的原生 TGZ/profile 安装流程。

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
claude plugin install codevow@ai-code-local
codex plugin add codevow@ai-code-local
```

`-plugin.zip` 用于市场分发，手动本地安装使用带市场的下载包。保留已注册
本地市场的解压目录。

## 更新与卸载

刷新市场用于获取最新目录。在系统终端更新已安装插件时，使用对应宿主的命令。

Claude Code：

```sh
claude plugin marketplace update ai-code
claude plugin update codevow@ai-code --scope user
```

macOS 上的 ZCode：

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace update ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins update codevow@ai-code
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

- [CodeVow 使用与配置](../plugins/codevow/docs/usage.zh-CN.md)
- [Agent Delegation 使用示例](../plugins/ai-agent-delegation/README.zh-CN.md)
- [CodeStack 范围与市场可用状态](../plugins/codestack/README.zh-CN.md)
