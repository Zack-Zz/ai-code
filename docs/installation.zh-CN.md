# 安装 ai-code 插件

[English](installation.md) | 简体中文

CodeVow **1.0.8**（`codevow`）和 CodeStack **1.0.1**（`codestack`）已发布到
共享的 **ai-code** 市场。实际可安装版本以[发行记录](../published/index.json)
和宿主刷新后的列表为准。两个插件分别安装，可以只使用其中一个，也可以同时使用。
[Agent Delegation](../plugins/ai-agent-delegation/README.zh-CN.md) 尚未发布。

## 选择你使用的应用

| 宿主 | 桌面端操作 | 终端操作 | 市场来源 |
|---|---|---|---|
| Codex | [桌面端](#codex-桌面端) | [CLI](#codex-cli) | `Zack-Zz/ai-code`，`main` 分支 |
| Claude Code | [桌面端 Code 页](#claude-code-桌面端) | [CLI](#claude-code-cli) | Claude 专用清单或 `Zack-Zz/ai-code#main` |
| ZCode | [桌面端](#zcode-桌面端) | [macOS 内置 CLI](#zcode-cli) | 根目录 `marketplace.json` 完整 URL |
| DeepSeek Harness | [桌面端](#deepseek-harness-桌面端) | [独立 CLI / Web](#deepseek-harness-cli) | DSH 原生索引或 Release TGZ |

用户无需克隆本仓库或构建插件。桌面端使用各应用的原生插件管理。
`sh` 命令块在系统终端执行，斜杠命令在编码助手会话内执行。每条命令成功后再执行下一条。
市场只需注册一次；已经使用正确来源注册时，跳过添加命令。

## 插件 ID 变更后的重装

| 卸载旧 ID | 安装已发布 ID | 版本 |
|---|---|---|
| `ai-code-workflow` | `codevow` | 1.0.8 |
| `ai-code-stack-standards` | `codestack` | 1.0.1 |

1. 刷新 `ai-code`，确认新入口可见且兼容当前宿主。
2. 通过宿主插件管理或下文 CLI 命令卸载已安装的旧 ID。新旧插件提供同名技能。
3. 安装、启用新 ID，再开启新会话。
4. 保留项目 `.ai-workflow/` 中的策略、任务和证据。

如果新版本已经安装，只需清理仍存在的旧 ID。旧入口从市场退役后，本机的旧安装
仍可能保留。不要手动修改插件缓存或全局配置。
详见[身份迁移指南](migrations/2026-10-27-plugin-identities.zh-CN.md)。

## Codex

### Codex 桌面端

1. 打开 **Plugins Directory（插件目录）**，选择 **ai-code** 来源。
2. 使用下方命令刷新来源，仅在来源不存在时先注册。重新打开目录，确认两个替代
   入口均可用；来源仍未显示时重启桌面应用。
3. 在已安装插件管理中卸载仍存在的 `ai-code-workflow`、`ai-code-stack-standards`。
   即使当前市场不再列出旧 ID，也可以使用下文的 CLI 卸载命令。
4. 分别打开 **CodeVow**、**CodeStack**，安装需要的插件并确认启用。
5. 核对版本为 **1.0.8**、**1.0.1**，再开启新聊天。

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref main
codex plugin marketplace upgrade ai-code
```

使用 Codex 原生市场注册，不需要手工修改 `config.toml`。
见 [OpenAI 官方市场指南](https://developers.openai.com/plugins/build/plugins#add-a-marketplace-from-the-cli)。

### Codex CLI

使用提供 `codex plugin` 的 CLI。市场不存在时才执行注册命令，再刷新：

```sh
codex --version
codex plugin marketplace add Zack-Zz/ai-code --ref main
codex plugin marketplace upgrade ai-code
```

迁移前先确认刷新后的市场中替代入口可见。仅对实际已安装的旧项执行对应卸载命令：

```sh
codex plugin remove ai-code-workflow@ai-code
codex plugin remove ai-code-stack-standards@ai-code
```

安装并检查两个正式插件：

```sh
codex plugin add codevow@ai-code
codex plugin add codestack@ai-code
codex plugin list --marketplace ai-code
```

预期显示 **installed, enabled** 及上述版本。市场读取
`.agents/plugins/marketplace.json`，使用固定 Git 子目录安装。
安装或卸载后开启新的 Codex 会话。

## Claude Code

使用 **Claude Code 2.1.224+**，本市场的 `archive` 来源要求该最低版本。
本节面向 Claude Code 本地会话，包含桌面应用的 **Code** 页；普通 Claude 聊天
和 Cowork 的安装方式不在本节范围。
见[来源版本要求](https://code.claude.com/docs/en/plugins/marketplace-reference#archive-plugin-source)。

### Claude Code 桌面端

1. 在桌面应用的 **Code** 页打开本地项目。
2. 点击输入框旁的 **+ → Add plugins（添加插件）**。如果菜单显示 **Plugins**，
   选择 **Plugins → Browse plugins**；启用、停用和卸载使用 **Manage plugins**。
3. 若未列出 `ai-code`，执行下面的 CLI 注册命令，再重新打开插件浏览器；
   已有来源则刷新。确认两个替代入口可用后再移除旧安装。
4. 在原安装范围卸载已安装的旧 ID。选择 **CodeVow**、**CodeStack**，
   按用户、项目或仅本地范围安装需要的插件。
5. 检查已安装版本和启用状态，再开启新会话。

```sh
claude plugin marketplace add "Zack-Zz/ai-code#main"
claude plugin marketplace update ai-code
```

同一机器上的本地桌面端与终端共享 Claude Code 设置。这不会把插件安装到云端
会话或另一台机器。见[桌面端插件指南](https://code.claude.com/docs/en/desktop#install-plugins)。

### Claude Code CLI

市场不存在时才注册 Claude 专用清单，再刷新：

```sh
claude --version
claude plugin marketplace add https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/.claude-plugin/marketplace.json
claude plugin marketplace update ai-code
```

迁移前先在刷新后的插件浏览器中确认替代入口可用，再卸载已安装的旧 ID。
以下按 `user` 范围举例；原来装在 `project` 或
`local` 范围时，改用相应范围。

```sh
claude plugin uninstall ai-code-workflow@ai-code --scope user
claude plugin uninstall ai-code-stack-standards@ai-code --scope user
```

为当前用户安装两个插件并检查结果：

```sh
claude plugin install codevow@ai-code --scope user
claude plugin install codestack@ai-code --scope user
claude plugin list
```

开启新会话，或在**已有 Claude Code 会话内**执行 `/reload-plugins`。
`/plugin` 的 **Installed** 页可查看范围和启用状态。技能以
`/codevow:workflow`、`/codestack:code-standards` 等名称显示。
见[安装及范围说明](https://code.claude.com/docs/en/discover-plugins)。

## ZCode

### ZCode 桌面端

1. 打开工作区，进入 **设置 → 插件**。
2. 进入 **创建 → 添加插件市场**，填写下面的完整 URL；已有来源正确时只需刷新：

   ```text
   https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json
   ```

3. 确认“个人”分段的 **ai-code** 市场中 **CodeVow 1.0.8**、**CodeStack 1.0.1**
   可用，再到“管理已安装”卸载已安装的旧 ID。
4. 安装 **CodeVow**、**CodeStack**，确认启用。
5. 核对已安装版本，再开启新会话。

使用完整 URL。仅添加仓库时，ZCode 可能选中 Claude 清单，其 `archive` 来源
不受 ZCode 安装器支持。若错误包含 `unsupported ... archive`，在“市场源”中
移除错误来源，添加上述完整 URL 并刷新。移除市场来源和卸载插件是两个操作。
见 [ZCode 插件指南](https://zcode.z.ai/cn/docs/plugin)。

### ZCode CLI

以下示例使用 **macOS 应用内置 CLI**，要求 ZCode 安装于 `/Applications/ZCode.app`，
且 `node` 在 `PATH` 中。安装位置不同时调整路径；其他平台使用上述桌面操作。

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/main/marketplace.json
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace update ai-code
```

已有正确来源时跳过添加。迁移前先在刷新后的桌面市场中确认替代入口可用，
再仅卸载实际已安装的旧项：

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins uninstall ai-code-workflow@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins uninstall ai-code-stack-standards@ai-code
```

安装、启用并检查两个插件：

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install codevow@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install codestack@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins enable codevow@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins enable codestack@ai-code
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins list
```

开启新会话，并检查 Plugin 技能分组。

## DeepSeek Harness

### 版本兼容性

安装前先区分插件版本及其声明：

| 插件来源 | DSH 要求 | 可用状态 |
|---|---|---|
| 已发布的 CodeVow 1.0.8 / CodeStack 1.0.1 安装包与索引 | `engines.dsh` 与 DSH peers 均最低 `>=0.2.1-rc.2` | 下文当前公开安装入口 |

最低版本范围接受 RC3 及更高版本，不再仅因精确 RC2 锁定而拒绝。
DSH 的范围匹配包含预发布版本（`includePrerelease`）；存在 `engines.dsh` 时
以它为准，只有缺少它时才回退到 DSH peer 要求。见
[官方兼容性规则](https://github.com/deepseek-ai/deepseek-harness/blob/master/packages/boot/app-boot/README.zh.md#profile)。
范围匹配不代表未来 API 兼容或完整宿主验收已经通过。

安装前在桌面应用的 **About DeepSeek Harness（关于）** 或实际 CLI 的 `--version`
核对版本。市场中不兼容条目的安装按钮可能禁用；安装 npm 或改用 TGZ 不会取消
版本检查。公开安装以[正式索引](../published/dsh/index.json)为准，旧发行保留原有声明。
不要把版本豁免当作兼容性证据。

[有界 RC3 桌面探针](../plugins/codevow/docs/verification/2026-10-28-dsh-reviewer-startup.md)
已验证发布前的 1.0.8 候选版原生安装、重启加载和一次只读 Reviewer 委派；完整桌面端和 Web
宿主验收仍为 **pending**，正式验收槽保持 null。CodeVow 需要 Agent Preset 服务和
spawn 后端；minimal/SDK/ACP profile 不在声明的试用范围。

### DeepSeek Harness 桌面端

**直接使用已安装的桌面应用。桌面端自带 Node/pnpm 安装运行环境，不需要另装
npm CLI，也不需要创建 Web 试用 profile。**

1. 按上文检查应用版本和插件兼容性。
2. 打开 **Plugins（插件）**，在 **Experimental plugins** 旁选择 **More**，
   开启 **Custom plugin markets（自定义插件市场）**。这是可选的内置功能。
3. 进入 **Discover → Add index source**；已有来源可用 **Manage index sources…**
   管理并刷新。添加：

   ```text
   https://raw.githubusercontent.com/Zack-Zz/ai-code/main/published/dsh/index.json
   ```

4. 选择 **CodeVow** 或 **CodeStack**，检查版本、兼容状态及固定 Git 提交/子目录，
   仅对**兼容版本**确认安装。刷新来源并选择 CodeVow 1.0.8 或 CodeStack 1.0.1，
   即可使用最低 `>=0.2.1-rc.2` 范围。
5. 在 **Installed** 页核对安装和 bundle 启用状态，必要时重启应用，再新建会话
   检查技能。

市场索引安装预构建 Git bundle。Release 中的 TGZ 是另一种原生包格式；插件
无需发布到 npm registry 才能进入市场。
见[桌面端内置运行环境](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.3/apps/desktop/README.md#application-overview)、
[自定义插件市场](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.3/packages/experimental/plugin-market-bundle/README.md#use-this-package)
及 [Discover](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.3/packages/client/ui-plugin-market/README.md#use-this-package)。

### DeepSeek Harness CLI

以下步骤启动独立 **Web profile**，与桌面端 profile 分开。命令将官方 npm 启动入口
固定在 RC2，作为与链接的公开安装包兼容的可复现试用基线。RC2 是最低支持版本，
RC3 及更高版本同样满足声明范围。准备 Node.js 24+，并确保 `pnpm` 在 `PATH` 中；上游仓库也
支持 22.x 范围内的 Node 22.19+。系统 pnpm 前置条件用于独立 npm CLI，
不适用于桌面端内置安装器。

下载 [CodeVow TGZ](https://github.com/Zack-Zz/ai-code/releases/download/codevow%2Fv1.0.8/codevow-1.0.8-dsh-plugin.tgz)
和 [CodeStack TGZ](https://github.com/Zack-Zz/ai-code/releases/download/codestack%2Fv1.0.1/codestack-1.0.1-dsh-plugin.tgz)，
以及各自 Release 的 `SHA256SUMS`。对照对应 `installers/` 条目核对 TGZ 哈希。
下面假设文件在 `$HOME/Downloads`；其他平台改为实际路径。

```sh
cd /path/to/your/project
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 --version
```

选择**未占用**的 profile 名，仅首次执行下一条命令：
**`--from-default-profile` 会替换已有同名 profile，包括插件依赖和用户 patch。**
不要对现有桌面端或个人 profile 执行该命令。

```sh
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 --profile ai-code-trial --from-default-profile web --dump-config
```

将预构建 bundle 安装到该 profile，检查配置后启动：

```sh
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 plugin --profile ai-code-trial add "$HOME/Downloads/codevow-1.0.8-dsh-plugin.tgz"
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 plugin --profile ai-code-trial add "$HOME/Downloads/codestack-1.0.1-dsh-plugin.tgz"
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 --profile ai-code-trial --dump-config
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 --profile ai-code-trial
```

打开终端打印的地址，默认为 `http://127.0.0.1:3080`。在 **Settings → Models**
配置并保存模型凭据，再用 **Choose workspace** 选择项目后开始会话。
以后只执行最后一条启动命令，不重复初始化 profile。Web 界面也可按上文的
Plugins 步骤通过市场索引安装。
见[官方 CLI 参考](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.2/apps/cli/README.md)
及 [Web 配置指南](https://github.com/deepseek-ai/deepseek-harness/blob/dsh-v0.2.1-rc.2/docs/user/guide/index.md)。

### Harness 首次使用与卸载

在兼容的新会话中，用 `/workflow` 调用 CodeVow，或用 `/code-standards` 调用
CodeStack。只读检查时，让助手列出这两个技能并读取指令，不修改项目文件。
`/review` 调用审查技能；其原生只读 Reviewer 仍需单独做运行验证。
技能可见不代表自动选用和任务结果已经通过验收。

桌面端在 **Plugins → Installed** 停用、卸载对应 bundle。独立 profile 使用
相同的固定版本 CLI，并指定实际安装插件的 profile：

```sh
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 plugin --profile ai-code-trial remove codevow
npx --yes @deepseek-ai/dsh@0.2.1-rc.2 plugin --profile ai-code-trial remove codestack
```

Git bundle 升级按同一宿主/profile 的卸载、安装兼容替代版本流程完成，必要时
重启。DSH 没有旧 ID 需要迁移。升级、卸载时不要加入 profile 初始化参数。

## 下载包安装

Claude Code、Codex 和 ZCode 从插件的公开
[Release](https://github.com/Zack-Zz/ai-code/releases) 选择对应宿主文件。

| 文件 | 用途 |
|---|---|
| `<ID>-<VERSION>-<HOST>.zip` | 包含市场元数据的本地市场下载包 |
| `<ID>-<VERSION>-<HOST>-plugin.zip` | 公开市场使用的纯插件安装包 |
| `<ID>-<VERSION>-dsh-plugin.tgz` | Harness 原生安装包，按上文宿主/profile 流程安装 |

下载同一插件、同一版本 Release 的 `SHA256SUMS`。ZIP 下载包核对 `downloads/`
条目，原生安装包核对 `installers/` 条目。将本地市场 ZIP 解压到稳定目录，
注册解压后的根目录，不要注册内部插件子目录：

| 宿主 | 解压根目录中的清单 | 注册 |
|---|---|---|
| Codex | `.agents/plugins/marketplace.json` | `codex plugin marketplace add /path/to/extracted` |
| Claude Code | `.claude-plugin/marketplace.json` | `claude plugin marketplace add /path/to/extracted` |
| ZCode | `marketplace.json` | 通过桌面市场界面添加该文件 |

从这些本地下载包声明的 **ai-code-local** 安装。例如
`codex plugin add codevow@ai-code-local` 或
`claude plugin install codevow@ai-code-local --scope user`。
注册期间保留解压后的源目录。

## 安装后检查

- 通过原生插件管理或宿主列表命令检查 ID、版本、来源和启用状态，避免新旧 ID 同时启用。
- 在新会话请求：“加载已安装的 CodeVow workflow 和 CodeStack code-standards 指令，
  告诉我是否都能读取；本次保持只读。”
- CodeVow 提供 `workflow`、`tdd`、`debugging`、`review`、`review-results`、
  `verification`；CodeStack 提供 `code-standards`。选择语法依宿主而异，
  不确定时使用技能选择器或自然语言请求。
- 包完整性、安装、技能可见性和实际行为分别检查。构建通过或列出技能不代表真实宿主验收。

## 更新和卸载

先刷新市场。目录刷新本身不能证明运行中的会话已加载新版本。
下表以 CodeVow 举例，操作 CodeStack 时替换成 `codestack`；需要时分别处理两个插件。

| 宿主 | 更新 | 卸载 |
|---|---|---|
| Codex | `codex plugin marketplace upgrade ai-code` 后在桌面管理中检查版本，仍旧时通过原生 remove/add 重装 | `codex plugin remove codevow@ai-code` |
| Claude Code | `claude plugin marketplace update ai-code` 后执行 `claude plugin update codevow@ai-code --scope user` | `claude plugin uninstall codevow@ai-code --scope user` |
| ZCode 桌面端 | 市场源刷新 `ai-code`，再在管理已安装中检查更新 | 已安装插件详情 → 卸载 |
| ZCode macOS CLI | 刷新市场后执行 `node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins update codevow@ai-code` | `node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins uninstall codevow@ai-code` |
| Harness | 刷新索引、检查兼容性，再按上文同一宿主/profile 卸载并安装 | Plugins → Installed，或上文固定版本的 profile 卸载命令 |

变更后重新加载或开启新会话，Harness 按需重启。市场源不再需要时单独移除。
不要因为卸载插件而删除项目 `.ai-workflow/` 记录。

## 故障处理与依赖

| 症状 / 功能 | 检查 |
|---|---|
| 找不到新 ID | 刷新正确的 `ai-code` 来源，对照发行记录。注册/移除来源与安装/卸载插件是两个操作。 |
| 重复的工作流或规范技能 | 清理已安装的旧 ID，再开启新会话。 |
| Claude 不支持 `archive` | 核对 2.1.224+ 和正确清单；交互面板仍拒绝时使用 CLI 安装路径。 |
| ZCode 不支持 `archive` | 将市场来源改为上文根目录 `marketplace.json` 完整 URL。 |
| Harness 安装按钮禁用 | 对照运行时与所选条目的 `engines.dsh`。当前 CodeVow 1.0.8 / CodeStack 1.0.1 声明 `>=0.2.1-rc.2`；刷新来源并选择这些版本。旧发行保留原有声明。 |
| Harness 已安装但无技能 | 检查 bundle 启用状态、重启/新会话、所需服务与 profile 兼容性，不从包安装推断激活。 |
| CodeVow 可选 Python 工具 | Python 3.11+；可选文件暂存需要 POSIX 文件操作。Markdown 技能本身不需要 Python。 |
| CodeStack | 不需要额外运行时，不依赖其他 ai-code 插件。 |

账号和模型由各宿主管理。尚未发布的 Agent Delegation 另需 Python 3 和配置好的
`agent-bridge/v1` CLI；[Bridge 配置](https://github.com/Zack-Zz/ai-mcp/blob/main/packages/agent-bridge/README.md#构建与受控配置)
还要求其支持的平台及已认证的目标编码工具。

## 下一步

- [CodeVow 使用和配置](../plugins/codevow/docs/usage.zh-CN.md)
- [CodeStack 规范](../plugins/codestack/README.zh-CN.md)
- [Agent Delegation 源码示例](../plugins/ai-agent-delegation/README.zh-CN.md)
