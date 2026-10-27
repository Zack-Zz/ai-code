# ai-code 架构与责任边界

[English](architecture.md) | 简体中文

ai-code 承载独立的 AI 编码插件。公共层负责注册、校验、构建、包检查和分发，
各插件负责自己的功能、配置和行为规则。开发入口见[开发指南](../CONTRIBUTING.zh-CN.md)。

## 仓库结构

```text
ai-code/
  catalog.json                    插件目录注册
  distribution.json               main 市场与宿主运输方式
  plugins/
    codevow/             CodeVow
    ai-agent-delegation/          Agent Delegation
    codestack/      CodeStack
  tooling/plugin_tool.py          公共 CLI
  tooling/plugin_tools/           通用校验、构建、检查与发行
  tests/                          公共测试和插件测试汇总
  docs/                           用户、开发与维护文档
  published/                      正式记录、市场回执与 Codex 安装内容
  .github/workflows/              CI、Release 与市场同步
```

构建输出放在显式指定的空临时目录；`dist/` 被 Git 忽略，不作为源码维护。

## 公共层与插件

| 组成 | 维护内容 |
|---|---|
| `catalog.json` | 插件目录的相对路径，不复制版本和资源 |
| 插件 `product.json` | 插件 ID、名称、版本、宿主、署名和资源白名单 |
| 插件目录 | 技能、配置、辅助工具、宿主适配、说明和行为测试 |
| 公共工具 | 从可信源码生成原生清单、安装包、市场、ZIP 和哈希 |
| 根 `npm test` | 独立运行公共工具和全部已注册插件的测试组 |

根 `package.json` 是 private 维护工具配置，不提供插件发行版本。未注册插件
不进入公共构建；入包文件必须位于插件自己的显式资源白名单中。

同一插件的共同资源在不同宿主包中保持同哈希，宿主适配和生成资源单独声明。
一个插件的规则不约束其他插件。公共层不要求所有插件拥有 CodeVow 的六技能、
Reviewer、策略或 `.ai-workflow` 任务记录。

## 市场与发行

源码和公开市场都使用 `Zack-Zz/ai-code` 的 `main`，市场名为 `ai-code`。
同一插件 ID 的市场入口指向最新成功同步的正式版本。

本地包使用独立名称，注册开发来源时不会复用公开市场身份：

| 市场名 | 来源与用途 |
|---|---|
| `ai-code` | main 公开市场 |
| `ai-code-local` | 公共构建及带本地市场的 Release 下载包 |
| `codevow-local` | CodeVow 自带构建工具的本地试用市场 |

| 输入或输出 | 职责 |
|---|---|
| `product.json` | 当前开发源码的版本和资源 |
| `published/index.json` | 已同步正式版本及记录引用 |
| `published/releases/ID/VERSION.json` | 正式发行、冻结源码和制品记录 |
| `published/marketplaces.lock.json` | 根公开清单的受管路径与哈希 |
| `published/codex/ID/VERSION/` | Codex 安装所需内容 |

开发版本与市场版本可以不同。`marketplace sync --output <空目录>` 生成开发
市场；`marketplace check` 只读检查公开快照。工具不会把开发源码直接当成正式
市场入口。版本使用 `X.Y.Z` 或 `X.Y.Z-preview.N`；预览版只公开为 GitHub
Prerelease，正式版成功发布并同步后进入市场。

Claude Code 和 ZCode 从固定 Release 附件安装。Codex 使用受管安装目录并固定
实际分发提交。市场部署先准备 Codex 安装目录，再更新发行记录、当前指针、
根清单和回执；路径、字节或基础提交发生变化时停止部署。

唯一手动构建/发布入口由 main 的可信工具冻结已提交的插件版本，自动派生规范
标签。build 对远端只读并导出原生安装包；publish 经 `plugin-release` 环境
创建或复用不可变标签，上传、回读并公开附件；正式成功后自动调用市场同步。
同步计划只读，部署经 `plugin-marketplace` 审核后写入。宿主验收是独立的事实
状态，不作为技术发布门禁。具体操作见
[发布指南](publishing.zh-CN.md)，数据要求见[证据契约](release-evidence.zh-CN.md)。

## 宿主与执行引擎

宿主是加载插件的编码助手；执行引擎是 Agent Bridge 启动或续接的独立会话。
两者使用不同的标识集合：

| 插件宿主 ID | 编码助手 | Bridge 引擎 ID |
|---|---|---|
| `claude` | Claude Code | `claude-code` |
| `codex` | Codex | `codex` |
| `zcode` | ZCode | `zcode` |

例如，在 Codex 中使用派发插件，把任务交给 Claude Code，宿主与目标引擎不同。
同工具派发需要用户明确要求独立会话。

原生包和市场路径由[渲染模块](../tooling/plugin_tools/rendering.py)维护。
当前 Codex 发行检查使用 skills-only profile；增加新的组件类型时，应独立
设计加载、权限和渠道要求。

## ai-code 与 ai-mcp

[ai-mcp](https://github.com/Zack-Zz/ai-mcp) 的 `@ai-mcp/agent-bridge` 负责独立
会话、任务恢复、进程控制和产物读取。ai-code 的 `ai-agent-delegation` 提供
派发技能、交接规范和调用外置 Bridge 的薄客户端。

```text
用户明确指定任务和目标工具
  → Agent Delegation 整理交接
  → agent-bridge/v1 CLI
  → Agent Bridge 管理任务和目标独立会话
  → 返回状态、改动与验证结果
  → 发起会话按原任务要求核对结果
```

| 责任 | ai-code | ai-mcp |
|---|---|---|
| 派发入口 | 明确用户意图、目标、范围和任务要求 | 检查调用者及执行权限 |
| 调用与结果 | 使用 Bridge 契约，展示状态和产物 | 提供 CLI/API、引擎发现、任务与产物操作 |
| 执行与恢复 | 按准确任务 ID 续接和回收结果 | 管理会话、进程、状态、恢复与取消 |
| 资源 | 插件技能、薄客户端、适配和安装包 | 引擎驱动、运行时与受控配置 |

插件不复制引擎驱动、凭据或本地任务服务。所用模型和账号由目标工具管理。
派发功能只在用户明确请求时使用，普通开发及原生子代理保持原有工作方式。

运行时用法见[Agent Bridge](https://github.com/Zack-Zz/ai-mcp/blob/main/packages/agent-bridge/README.md)，
插件用法见[Agent Delegation](../plugins/ai-agent-delegation/README.zh-CN.md)。

## DSH 原生组合包与发布状态

`dsh` 是第四个插件宿主，不是 Agent Bridge 引擎。CodeStack 只贡献标准
skill-filesystem 提供方；CodeVow 增加原生 spawn 工具与独立 Reviewer preset，
scope guard 约束原生工具，不实现第二套 agent 循环。安装展示采用 DSH locale。

当前源码 codevow/codestack 与不可变的旧公开记录分离。可信分发配置中的替代
映射仅在正式同步成功后成为永久退役事实。DSH 安装目录为
published/dsh/ID/VERSION，插件索引为 published/dsh/index.json。schema-3 Git
安装按宿主绑定实际安装提交；暂存回执使 D 中间态在市场 C 更新前也可验证。
历史快照仍按原版本读取。
