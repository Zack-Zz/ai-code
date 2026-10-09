# ai-code 架构与责任边界

日期：2026-10-08（Asia/Shanghai）。本文说明现行多插件结构与候选扩展；
实现与真实宿主验收分别见[本轮记录](reviews/2026-10-08-agent-delegation-implementation.md)。

ai-code 是承载多个 AI 相关插件的仓库。公共层提供注册、源校验、构建、
包检查、市场生成和发布准备；插件各自定义用途、资源与支持声明。CodeVow
（`ai-code-workflow`）是现有一个插件，不代表公共层必须采用它的工作流。

## 现行结构

```text
ai-code/
  catalog.json                    插件路径注册
  tooling/plugin_tool.py          公共 CLI
  tooling/plugin_tools/           通用校验、构建、检查、市场与 release
  tests/                          公共测试和已注册插件测试汇总
  docs/                           公共契约、架构与设计
  plugins/
    ai-code-workflow/             CodeVow 独立源码、清单、适配和测试
    ai-agent-delegation/          明确派发技能、三宿主资源和 Bridge 薄客户端
  dist/                           生成包、ZIP、聚合市场与发行索引
```

| 层       | 权威输入及职责                                                   | 验证范围                                                     |
| -------- | ---------------------------------------------------------------- | ------------------------------------------------------------ |
| 注册表   | `catalog.json` 只登记 `plugins/<目录>` 的相对路径                | 拒绝重复、未知字段、缺失及逃逸目录；未登记目录不进入发行构建 |
| 插件     | `plugins/<id>/product.json` 独立维护身份、版本、宿主和资源白名单 | 资源闭包、技能声明、适配与插件自有行为                       |
| 公共工具 | 根据可信源码输入生成原生元数据、包、市场、ZIP 和哈希             | 独立重算实际文件与哈希，拒绝链接、缓存、目标冲突和未登记文件 |
| 公共门禁 | 发现各已注册插件的受控测试入口，分组运行                         | 以退出状态汇总，空组、启动错误、异常退出和信号终止均失败     |
| 宿主     | 原生加载插件及执行技能或组件                                     | 必须以对应版本、包字节和真实会话验收；静态通过不能代替       |

根 private `package.json` 不提供插件发行版本。共同资源在同一插件的不同
宿主包中保持同哈希，宿主适配和生成资源分别声明。改动一个插件时，应验证
兄弟插件自身的内容和来源哈希不变；聚合市场可因成员变化而更新。

公共层不读取 CodeVow 的策略来决定其他插件行为，也不强制其他插件拥有
Reviewer、六份技能或 `.ai-workflow` 状态。插件目录中的 `AGENTS.md` 与
行为测试只约束该插件。`dist/` 是可重建产物，不能反向成为元数据权威。

## 宿主与执行引擎是两种标识

公共构建现行宿主 ID 为 `claude`、`codex`、`zcode`。源码
[`rendering.py`](../tooling/plugin_tools/rendering.py) 的 `manifest_path`、
`marketplace_path` 和 `package_files` 分别决定原生清单、市场路径及生成资源。

| 插件宿主 ID | 面向的产品  | 拟议 Bridge 执行引擎 ID |
| ----------- | ----------- | ----------------------- |
| `claude`    | Claude Code | `claude-code`           |
| `codex`     | Codex       | `codex`                 |
| `zcode`     | ZCode       | `zcode`                 |

宿主是加载 ai-code 插件的环境；引擎是 Bridge 启动或续接的独立 Agent
执行端。在 Codex 中加载插件并派发给 Claude Code 时，两者当然不同；用户
明确要求同工具独立会话时，引擎可以相同，会话身份仍必须不同。

当前公共构建能够生成三宿主资源包。该事实不证明任何新插件的自动调用、
CLI 执行或 MCP 加载。Codex 当前发布检查采用 skills-only profile：
[`metadata.py`](../tooling/plugin_tools/release/metadata.py) 的
`validate_listing` 拒绝 `mcpServers` 等清单字段和 `.mcp.json` 等资源。
普通资源可打包与该 profile 可发布是不同判定。

## 跨仓库边界：插件规范与技术运行时

跨 Agent 工具派发需要独立会话、任务恢复、进程控制和产物读取。这些能力
由 ai-mcp 的 `@ai-mcp/agent-bridge` 独立模块承担；ai-code 新增独立
插件 `ai-agent-delegation`，提供用户意图识别、交接规范、验收与调用指引。
该插件已有独立 product.json、测试和 catalog 登记，版本 0.1.0 候选；完整
三宿主派发闭环仍未验收，不进入正式发布支持声明。

```text
人类在发起 session 明确派发
  → ai-code / ai-agent-delegation 技能与宿主适配
  → agent-bridge CLI 或经过验证的 MCP 传输
  → ai-mcp / @ai-mcp/agent-bridge application 服务
  → 独立本地任务服务与 claude-code / zcode / codex 适配器
  → 目标独立 session 的结果和证据
  → 发起 session 验收与后续决策
```

| 责任       | ai-code                                                              | ai-mcp                                                    |
| ---------- | -------------------------------------------------------------------- | --------------------------------------------------------- |
| 何时派发   | 技能限定用户明确跨工具或同工具独立会话派发，组织目标、范围、验收条件 | 不推断普通开发需求为派发授权                              |
| 调用契约   | 文档、宿主适配、必要的薄 client 辅助                                 | 版本化 DTO、确定性校验、CLI/MCP application 服务映射      |
| 执行与恢复 | 展示可核验状态、结果和限制，交回发起 session                         | 引擎探测、任务/会话绑定、进程生命周期、持久化、恢复和产物 |
| 包与依赖   | 插件自身白名单、测试、宿主包及支持声明                               | 独立模块的发布、运行与引擎兼容测试                        |
| 权限       | 不把技能文本或 `approved=true` 当成人类授权证明                      | 对绑定、权限与幂等做确定性校验，拒绝不合法请求            |

ai-code 不复制引擎驱动或本地任务服务，不内嵌原生执行器、凭据和运行时，
也不安装用户全局配置。ai-mcp 的模块边界见
[ai-mcp 架构](../../ai-mcp/docs/architecture.md)；执行契约见
[Agent Bridge 模块设计](../../ai-mcp/docs/modules/agent-bridge.md)。

双方使用 `apiVersion: agent-bridge/v1`，执行引擎使用表中的 canonical ID。
Bridge 可执行名为 `agent-bridge`，提供引擎发现、preflight、任务和产物
操作；MCP 的 `agent_bridge_start`、`agent_bridge_get` 等工具映射同一个
application 服务。CLI 与 MCP 可有不同的传输外壳，语义、错误与权限判定
必须一致。详细 DTO、状态与恢复规则由 ai-mcp 模块文档维护，插件不另建一套。

## 插件启用与支持策略

派发插件只处理明确派发。普通实现、讨论、代码审查、原生 subagent 调用，
或“多找几个人看看”而没有独立工具/会话意图，都不因此切换工作模式。
调用者与执行者对等；发起 session 负责接收结果并按原请求验收，不能把
外部 Agent 的自述直接当成最终通过。插件不强制 review 流水线或固定模型。

Claude Code、ZCode 的模型由各工具当前可用的原生配置决定，官方或第三方模型均可。插件选择的是工具与独立会话，不按模型品牌筛选目标，也不自行切换模型、供应商或账号。ai-mcp 负责验证相应原生配置下的实际操作能力；配置读取问题与模型品牌分别记录。

自然语言“交给 Claude Code 实现”是语义明示；显式技能名或 CLI 是操作
入口。若产品要覆盖自然语言入口，Codex 技能界面应允许隐式加载，再在技能
内限制明确派发语义。加载技能与获得执行授权分别判断，不能设置
`allow_implicit_invocation=false` 后又承诺自然语言自动加载。

首版候选路径为“技能规范 + 外置 BridgeCLI”：先以准确 ID 支持独立、
持久、可续接会话，再验收三引擎的实际能力。桌面可见性单列后续实测门槛。
原生 MCP 加载需独立证明配置发现、启动、认证、权限和工具调用，并审查
对应宿主 release profile；本轮不扩展现行 Codex skills-only 规则。

## 文档权威与验证导航

| 阅读目的                 | 文档或源码                                                                                                  | 使用原则                                         |
| ------------------------ | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------ |
| 新插件最小接入及现行字段 | [插件作者指南](plugin-authoring.md)                                                                         | 宿主和资源声明以现行指南及校验源码为准           |
| 多插件迁移背景           | [2026-10-07 多插件规格](design/2026-10-07-multi-plugin-design.md)                                           | 保留历史日期；其中两宿主表述已早于现行三宿主契约 |
| 发行渠道与证据           | [发布指南](publishing.md)、[验收契约](release-evidence.md)                                                  | 区分 draft/stable、包完整性与真实宿主行为        |
| CodeVow 自身行为         | [CodeVow AGENTS](../plugins/ai-code-workflow/AGENTS.md) 及插件文档                                          | 不扩散为兄弟插件的公共契约                       |
| 独立派发插件             | [2026-10-08 插件设计](design/2026-10-08-agent-delegation-plugin-design.md)                                  | 候选源码已登记；完整宿主派发闭环未验收           |
| 技术运行时及模块         | [ai-mcp 架构](../../ai-mcp/docs/architecture.md)、[Agent Bridge](../../ai-mcp/docs/modules/agent-bridge.md) | 运行时和状态语义由对应模块维护                   |

现行统一门禁为根 `npm test`。源校验、空目录构建及可信源码包检查的命令
见作者指南。新插件实现应先有有效失败测试，再做最小实现和对应宿主实测；
仅设计文档不需要运行整套代码测试。设计阶段文档自查只证明范围与引用，
候选实现的工程、原生与Git交付记录见下方，不能互相替代。

2026-10-09 开发收口：插件功能与公共多插件接入已有候选源码；当前用户
明确授权完成开发、review通过后commit/push，不扩展为安装或正式发布。
Bridge默认Codex app-server、停止确认和ZCode宿主入口限制见
[开发收口记录](../../ai-mcp/docs/reviews/2026-10-09-agent-bridge-development-delivery.md)。
