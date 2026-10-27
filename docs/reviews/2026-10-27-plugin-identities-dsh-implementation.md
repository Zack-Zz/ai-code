# 插件身份统一与 DSH 原生支持实施记录

日期：2026-10-27（Asia/Shanghai）。状态：本地实现、Review 与验证完成；未提交、推送或发布。

后续版本更正：用户明确指定当前未发布候选为 CodeVow `1.0.6`、CodeStack `1.0.0`。
下方原始候选表与验证数量保留此前记录，`2.0.0` / `0.2.0` 不再是当前目标；
旧验证结果不作为更正后版本的通过证据，新结果见[用户指定候选版本复验](#用户指定候选版本复验)。
当前规则见[插件版本升级规范](../publishing.zh-CN.md#插件版本升级规范)。

## 实施结果

| 插件 | 当前源码 | 候选版本 | 声明宿主 |
| --- | --- | --- | --- |
| CodeVow | `plugins/codevow/`，ID `codevow` | 2.0.0 | Claude Code、Codex、ZCode、DSH |
| CodeStack | `plugins/codestack/`，ID `codestack` | 0.2.0 | Claude Code、Codex、ZCode、DSH |
| Agent Delegation | `plugins/ai-agent-delegation/`，身份保留 | 0.1.0 | 原三个宿主，未增加 DSH |

两个候选版本都通过版本工具先预览再应用；142 个冻结公开文件已与 HEAD 逐字节核对一致。四端 acceptance 仍为 null，publication_ready 为 false。项目 `.ai-workflow` 的 policy/tasks/evidence 数据契约保留；可选 files 暂存和回执按新 ID 隔离，旧 ID 未应用计划被拒绝，须重新生成。

- 当前 catalog、CI、源码维护入口和双语操作文档使用新 ID。旧公开市场、固定安装目录和历史发行记录保持原字节，只有未来成功的正式部署才会切换入口。
- 两个 DSH bundle 使用官方 package.json、dsh.bundle.patch、独立 skill-filesystem provider 和原生 profile 安装。
- CodeStack 仅有声明式适配、Markdown 和静态资源；DSH 小图是原图的宿主专用派生资源，原 PNG 和固定历史 URL 保留。CodeVow DSH 使用已有 SVG。
- CodeVow 原生 Reviewer 使用 spawn、独立 preset、工具可见性限制和最终 guard，覆盖创建、切换、恢复、销毁和卸载；共享审查合同只维护一份。
- 公共工具支持 schema-2 产品、宿主专属/固定生成资源、DSH npm TGZ、独立闭包检查、schema-3 发行与 Git 安装记录，以及旧 schema 的只读验证。
- 分发实现 active/retired、双 Git D、暂存 receipt、C 原子消费、固定 Git 索引、失败恢复和旧 ID 禁止复活。无 receipt 的未记录安装目录始终拒绝。
- workflow 和 Java 长内容拆为共享 references；所有声明宿主保留共同资源同字节。

## 上游兼容调整

原方案研究的是固定 master 提交 `22ddee3792402c3e70ec5f86a63c3e3e895a2f60`，包版本为 RC3。实际 npm 核对发现可安装版本为 `0.2.1-rc.2`；RC3 独立 native executor 包不存在于当时公开注册表。

实现改为精确的公开 RC2 API：`@deepseek-ai/dsh-agent-tool-presentation` 配置 `mode: native`，子代理配置 `modelSelectionSettings: false`。engines 和 peer 约束与实际隔离安装版本一致。该调整已同步设计及当前双语文档，没有声明 RC3 可用。

## 验证记录

所有构建和模拟发行均在临时目录，未创建本仓库标签或操作远端。

| 检查 | 本轮结果 |
| --- | --- |
| `validate --all` | 通过，三个注册插件 |
| 根 `npm test` | 6 组全部通过；公共 Python 341、CodeVow Python 327、Agent Delegation Python 35，另含汇总器和两插件 Node 技能组 |
| `npm run lint` | 通过，ESLint 与 Markdownlint |
| `check_no_dist.py` / `git diff --check` | 通过，无跟踪的 dist 输出 |
| 全部声明宿主构建及逐包可信源检查 | 11 包通过，包括两个插件的 DSH 包 |
| 两候选版本 draft release check/prepare/verify | 通过，CodeVow 331 文件、CodeStack 139 文件；四端仍 pending |
| 当前公开快照与冻结源检查 | 通过，旧版本继续有效；没有 pending distribution |
| 当前文档相对链接 | 当前根文档、迁移、设计及本记录 191 个引用无缺失；此前连同插件入口共 227 个引用无缺失 |
| DSH 已发布 API 组合 | 13 项通过，官方 DSH RC2 / Cordis 4.0.5，Node 24.4.1 |

临时制品及验证日志：`/private/tmp/ai-code-verified-20261027-ze3p_wp8/`，包含 `report.json`、`checks.log`、11 个包和两个 draft release bundle。统一门禁日志为 `/private/tmp/ai-code-reviewed-final-suite.log`；Review 回归为 `/private/tmp/ai-code-review-regressions.log`。这些是本地临时证据，不进入发行包。

原生 API 测试可重放：

```sh
DSH_NATIVE_NODE_MODULES=/private/tmp/codevow-native-api/node_modules node plugins/codevow/tests/dsh/native-api.mjs
```

该脚本对精确官方依赖版本、实际 YAML 配置的 Config schema、两个 provider 共存及卸载、真实 renderSkillContent、串行首轮限制、隐藏工具拒绝、own-scope 绕过拒绝、预设双向切换、其他 Agent 不受影响、reload、创建失败回滚和销毁作出断言。workflow 实际渲染为 7,757 个 Unicode 码点，低于默认 8,192 修剪阈值。

缺失 `DSH_NATIVE_NODE_MODULES` 时入口返回非零，不以缺依赖的 skip 充当通过。依赖和缓存安装在隔离临时目录，没有安装用户宿主或 profile。

## Review 与修复闭环

主代理完成集成自审；两个实现代理分别负责插件和分发模块；另由独立 code_reviewer 检查公共制品与发布一致性。独立 Review 没有确认 critical/high，确认两项 medium，均在本轮授权范围内修复并复审通过：

1. **恢复 C 时原计划绑定不足。** 新回归分别篡改 receipt 的 plan_hash、config_hash 和 base_commit，原实现三项均失败。实际部署消费入口现在先回到原 B 重建配置/计划并回到 S 重建制品，核验所有 pending receipt；以已抓取的 origin/main 验证祖先关系，兼容 checkout 位于冻结 S 的恢复。之后才核对真实 Release 并允许写入。纯数据 check_plan/finalize 不冒充有 Git 上下文的验证器。
2. **TGZ 元数据预算和 sparse 类型缺口。** 新回归先复现 PAX 总解压预算绕过及零字节 sparse 被当作普通文件。读取器现在先限制整个 gzip 解压流，再交给 tarfile，并只接受确切普通成员且拒绝 sparse。正常 TGZ 的内容和确定性回归保留。

两项 targeted RED 均为真实功能失败；修复后的相关部署及 DSH 回归 35 项通过。独立 Reviewer 对修复重新读取源并执行纯内存复验，通过了这两项修复；完整统一门禁由主代理运行。

## 后续 Review 修复与复验

用户在后续只读 Review 后授权修复两项新发现的问题，继续保持不提交、不发布。
本节记录后续结果；上面的初次验证记录保留原测试数量和边界。

1. **P1：Reviewer 搜索插件缺少 RC2 必填配置。** 新增
   `plugins/codevow/tests/dsh/native-preset.mjs`，纳入同目录的 `native-api.mjs` 入口。
   测试先构建两个实际 DSH 包，再经官方
   `loadOverlayPatches`、`composeEntries`、Loader 和 PresetRegistry 激活未经改写的
   overlays。修复前因 `sampleOverCapGlobResults missing required value` 退出 1；
   搜索插件补充 `sampleOverCapGlobResults: false` 后退出 0。现在覆盖完整预设激活、
   挂载、真实工具列表仅为 read/grep/glob，以及两个包的七技能与 provider 身份。
2. **P2：DSH 制品可声明旧发行格式绕过安装器检查。** `layout` 按产品宿主限制
   schema；`historical` 独立要求 DSH 的 release 与 package index 均为 schema 3。
   新增 `test_release_schema.py` 四个测试，修复前七个子断言有效失败，包含 schema 1
   删除全部安装器并重算校验信息、schema 2 降级、索引降级、两条验证入口和正常
   schema 3。无 DSH 的旧三宿主 schema 1/2 兼容测试保留。

一个 code_implementer 负责独立的发行格式修复，主代理负责 Reviewer 修复与集成；
随后独立 code_reviewer 只读复核两项修复和相关调用，未发现阻塞或应修复项。
Reviewer 仅有指令层只读限制（policy_only），不是工具层写保护。主代理完成集成自审，
并对两个实际候选制品分别降为 schema 1/2、完整重算校验信息，确认两入口均拒绝接受。

| 后续检查 | 结果 |
| --- | --- |
| 根 `PYTHONDONTWRITEBYTECODE=1 npm test` | 6 组通过；公共 Python 345、CodeVow Python 327、Agent Delegation Python 35，另含 Node 组 |
| schema/installers/dsh 定向测试 | 21 项通过，独立 Reviewer 亦重放通过 |
| 隔离官方 RC2 原生入口 | 16 项通过，独立 Reviewer 亦重放通过；包含新增真实 Loader 预设激活路径 |
| 全部宿主构建、可信源码逐包检查 | 11 包通过 |
| 两候选版本 draft prepare/verify 与 historical | 通过；schema 3，CodeVow 331 文件、CodeStack 139 文件；acceptance 仍 pending |
| `validate --all`、`npm run lint`、`git diff --check`、`check_no_dist.py` | 通过 |
| 公开市场快照检查 | 通过，无 pending distribution；公开文件未修改 |
| 本轮修改的双语维护文档相对链接 | 37 项无缺失 |

后续制品和降级复验报告：`/private/tmp/ai-code-two-fixes-rlcd66xc/` 中的
`report.json`、`downgrade-regressions.json`。全量门禁日志为
`/private/tmp/ai-code-two-fixes-suite.log`；原生 RED、GREEN 与最终日志分别为
`/private/tmp/ai-code-fix-native-red.log`、`/private/tmp/ai-code-fix-native-green.log`、
`/private/tmp/ai-code-fix-native-final.log`。这些临时证据不进入发行包。

当前双语开发指南、原生测试说明与发布指南已同步真实覆盖范围及 schema 约束。
16 项检查证明官方 Loader 的完整预设激活、挂载和工具注册；Agent 仍为合成对象，
未运行模型、真实 spawn 会话、用户 profile 或真实文件工具操作。此结果不提升任何
宿主 acceptance 槽；后续 Git、发行、安装仍须各自明确授权。

## 用户指定候选版本复验

用户明确指定 CodeVow `1.0.6`、CodeStack `1.0.0`。远端 Release 回读仍只有旧 ID
下的 CodeVow `1.0.5` 和 CodeStack `0.1.0` 等既有发行，没有发布被更正的候选。
新插件的初始正式版本为 `1.0.0`，后续默认只增加一个补丁版本；用户明确指定目标
版本或升级级别时按该要求执行。旧 `0.x` 已发布历史不回写。

本轮更正未发布候选的 `product.json` 与当前说明章节，写入前独立预览四个文件的
前后哈希。通用版本工具的拒绝降级逻辑未修改；没有有效宿主证据引用或生成摘要
需要移除，四端 acceptance 继续为 null。当前双语导航、安装包文件名、制作示例、
迁移表、发布规范、根规则及维护技能同步更新；旧设计和验证数字保留历史语境。

主代理完成元数据与双语 diff 自审；一个 code_implementer 负责独立的文档同步。
这是元数据与文档更正，不含运行时代码变化，未编写仅检查文案的回归测试。

| 更正后检查 | 结果 |
| --- | --- |
| 公共版本与本地版本准备测试 | 24 项通过 |
| CodeVow 版本、preview 独立包与回执测试 | 6 项通过；使用 Python 3.14 重跑，最初误用系统 Python 3.9 的环境失败不计通过 |
| 两插件 Node 技能契约组 | 通过，包含 CodeStack 四宿主构建与发行集成测试 |
| 公共源校验、CodeVow 独立源校验 | 通过，版本为 1.0.6 / 1.0.0 |
| 全部宿主构建与逐包可信源检查 | 11 包通过，两个插件各四包的版本字段均与用户指定一致 |
| 两候选 draft prepare/verify 与 historical | 通过，schema 3；CodeVow 331 文件、CodeStack 139 文件，publication_ready=false |
| 维护技能、ESLint、Markdownlint、相对链接、diff 与 dist 检查 | 通过 |
| 公开市场快照检查 | 通过，无 pending distribution；公开文件未修改 |

制品与报告：`/private/tmp/ai-code-version-correction-3rf0it9p/report.json`。
版本预览：`/private/tmp/ai-code-candidate-version-correction-preview.json`。
测试日志：`/private/tmp/ai-code-version-correction-tests.log` 与
`/private/tmp/ai-code-version-correction-codevow-tests.log`。本轮未重跑全量 `npm test`、
远端 CI 或真实宿主验收，先前提交的 CI 通过不作为当前未提交版本的通过证据。
本轮没有提交、推送、创建标签、发布或安装。

## 验证边界与后续

原生 API 组合使用真实 Cordis/Tools/AgentRegistry/Skill 服务，以及合成 Agent/工具定义。没有执行带模型的完整 Web profile、真实文件工具、用户工作区沙箱、真实 spawn 会话或安装升级验收，不能将 13 项 API 检查写成全部 H01–H09 通过。

真实 GitHub Actions、标签冻结、远端附件发布与回读、市场部署、用户重新安装均未执行。已有 acceptance 槽保持 null。公开 index 不会因为本地实现完成而改成新 ID，用户当前仍可使用已发布旧版本。

后续在用户 Review 本地改动并另行授权 Git/发行后，才进入冻结源码、公开 Release、D/C 市场切换和用户原生重新安装。新索引与新 ID 命令在对应正式入口出现后使用。

参见[设计及实施调整](../design/2026-10-27-plugin-identity-and-deepseek-harness-support.md)、[身份迁移](../migrations/2026-10-27-plugin-identities.zh-CN.md)、[安装指南](../installation.zh-CN.md)与[发布指南](../publishing.zh-CN.md)。
