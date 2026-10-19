# CodeStack 实现、验证与 Review 交付

日期：2026-10-18（Asia/Shanghai）。状态：开发及本地技术验证完成，等待用户 Review；完整原生验收 pending。

本文件保留首轮交付记录。后续全面 Review 的四点修复及新增行为证据见
[边界修复与行为复核](2026-10-18-codestack-boundary-fixes.md)；下文旧哈希与运行结果不代表修复后的当前状态。

## 1. 本次交付

插件名称 CodeStack，ID `ai-code-stack-standards`，开发版本 `0.1.0-preview.1`。
实现依据为用户批准的 [P1—P6 计划](../design/2026-10-18-codestack-plugin-design.md)
及 [中文规则稿](../design/2026-10-18-codestack-java-constraints.md)。

执行内容只有一个英文 [code-standards Skill](../../plugins/ai-code-stack-standards/skills/code-standards/SKILL.md)
和四份英文 reference：

| 层 | 负责的要求 |
| --- | --- |
| Java | 注释语言优先级；手写字段、方法、构造函数和参数的多行 Javadoc；核心逻辑行注释；生产构造与测试实例的边界 |
| 数据访问 | 禁止逐条及隐藏查询；批量输入与结果边界；租户、顺序、重复及缺失语义；实际 SQL 次数、范围与表影响 |
| JPA | 映射和生命周期、隐式加载及写入、删除传播、集合分页、实际 provider 与批量效果 |
| MyBatis | Java/XML 绑定、动态条件、嵌套查询、分页与实际批量执行 |

Skill 按本次任务及调用路径选择 reference，支持同一操作同时使用 JPA 和 MyBatis。
明确区分 MapStruct、仅 dependencyManagement、测试依赖、Hibernate Validator、未知存储、
持久化注解变更和仅文档注释变更。不要求业务项目增加配置或规则文件。

新增三个宿主适配、product 资源白名单、许可证、双语用户说明、匿名评测输入和测试入口。
根目录只登记插件路径并更新源码导航；没有修改公共构建工具、CodeVow、公开市场、
`published/`、全局配置或宿主缓存。执行规则和示例只有英文，中文保留在设计及维护记录中。

## 2. 自动化契约与失败证据

### 插件发现及资源闭包

先运行插件发现断言：公共 `list` 命令正常完成，但尚未登记 CodeStack，
`The successful public list response must include CodeStack.` 断言失败，退出 1。
创建插件并登记 catalog 后，同一测试退出 0。环境错误没有作为 RED。

新增 9 个插件契约测试，覆盖：

- 真实公共工具发现插件。
- 从独立临时源码构建三个宿主包，并使用可信仓库工具独立复验。
- 包含且仅包含四份 reference，执行资源与源码字节一致，开发说明及评测输入不入包。
- 包内容篡改、失效引用、资源白名单遗漏、Codex 技能绑定错误被拒绝。
- 空测试组、失败子进程和信号终止均传播失败，不能用标准输出中的 PASS 隐藏失败。

修复了测试入口在嵌套 node:test 环境中继承 `NODE_TEST_CONTEXT` 的问题，
子进程使用独立测试上下文；这不改变插件运行内容。

### 真实 SQL 计数器校准

隐藏查询 fixture 使用本机已有的 H2 2.3.232、纯内存数据库和冻结检查器，未下载依赖。
独立 Review 发现旧计数器只识别 SELECT 后接单个空格的前缀，逐条 CTE 查询被错计为 0 并错误通过。
先固定此反例，外层“应当拒绝”的断言退出 1，再修改检查器。

修后累加引擎记录的语句执行次数，仅排除完整匹配的统计观察语句；
在操作前后取差，避免把初始化混入本次预算，并关闭测试库观察结果复用。
独立重新编译、运行得到：

| 检查 | SQL 执行增量 | 退出状态 |
| --- | --- | --- |
| 普通 SELECT、CTE、前置注释、SELECT 后换行、重复执行、结果含统计表名 | 每种 1 | 校准通过，0 |
| 仅读取统计 | 0 | 校准通过，0 |
| 原始逐条查询 fixture | 4 | 观察模式 0；预算检查 1，符合预期 |
| 等价逐条 CTE 反例 | 4 | 预算检查 1，符合预期 |
| 手工批量正向控制 | 1 | 预算检查 0 |

正向控制是检查器校准，不能记作模型修复成功。H2 校准也不代表实际 JPA/MyBatis 行为、
生产执行计划或性能收益；它不进入统一门禁的强制依赖。

## 3. 最终本地验证

| 检查 | 结果 |
| --- | --- |
| `python3 -B tooling/plugin_tool.py validate --all` | 退出 0，所有已登记插件通过 |
| `PYTHONDONTWRITEBYTECODE=1 npm test` | 退出 0，6 个测试组通过 |
| 新插件定向 `node plugins/ai-code-stack-standards/tests/skills/run-skills.js` | 退出 0，9 个测试通过 |
| `npm run lint` | 退出 0 |
| `python3 .github/scripts/check_no_dist.py --root .` | 退出 0，无跟踪的 dist 文件 |
| CodeStack 三宿主 `build` | 退出 0，临时目录构建成功 |
| 三宿主各自 `package check --root .` | 均退出 0，独立检查通过 |
| Java 基础 fixture 编译与运行 | 注释语言、测试构造起始检查通过 |
| H2 校准及正负控制 | 符合上表预期 |

统一门禁包含汇总器自测、公共 Python 320 项、CodeVow 技能契约及 Python 324 项、
Agent Delegation Python 35 项、CodeStack 9 项；不同测试框架的计数不合并为一个模型成功率。

本次构建使用未提交工作树，基准 HEAD 为 `a62b7b42461ffda5fd6168a6197f060492760877`。
最终插件执行源码哈希：

```text
d5bebfb55eb5cfdd9523733f12bca6dcd858d6e7e5417b67a6da1b814a7bcb98
```

| 宿主包 | package_content_hash |
| --- | --- |
| Claude | `ca528ba4ae01050748a612ae710680e21106e0c440de64c259ea82a7b2abe32c` |
| Codex | `aa761edc52f9694cb82327a4431a177190340b19dd597353a8083ecbacba54b5` |
| ZCode | `05f6dfecf74d317ef60c864906c50b41b44eeabef018223d7253cadb29d6f20c` |

六个共同文件为 LICENSE、SKILL 和四份 reference。Claude/ZCode 另有清单；
Codex 另有清单和生成的技能接口。构建索引中的文件数不包含独立的 artifact 元数据。

## 4. Codex 原生技能发现试运行

使用 Codex CLI `0.163.0` 与当前配置模型 `gpt-6-astra`，未另选模型或推理档位。
R02 仅运行一组基线 / 候选，每边 1 次；相同初始文件、中文普通任务和模型环境，
候选增加临时工作区 `.agents/skills/code-standards` 源码副本。
两边都处于现有 CodeVow 环境。没有安装插件或修改全局配置。

固定任务原文：

> 请给 src/RateLimit.java 增加 public boolean permits(int requestedUnits)，请求数量不能为负数，小于或等于限额时允许，并在 test/RateLimitCheck.java 中补充边界检查。仅修改这两个文件。已确认此实现方案，直接完成并编译验证，不要操作 Git、安装依赖或修改其他目录。

| 观察 | 基线 1 次 | 候选 1 次 |
| --- | --- | --- |
| CodeStack 读取轨迹 | 未读取 | 实际工具读取 SKILL，随后只读取 Java reference |
| 新方法文档 | 英文多行 Javadoc，包含参数、返回和异常 | 同左 |
| 实际行为 | 边界允许、超限拒绝、负数抛异常 | 同左 |
| 独立冻结行为检查 | 通过 | 通过 |

冻结行为检查独立编译生成的生产类，不依赖模型生成的测试，覆盖容量 0、5、最大整数，
等于边界、超限以及负数。另检查实际声明与文档，不能用行为检查代替 Javadoc 审阅。

此结果支持“临时工作区原生 Skill 发现能自动选用本规则”这一有限观察。
基线已经正确，**没有证明编码效果改善**。源码 Skill 发现不是宿主插件清单加载、
安装/升级链路验收，也不是全部任务都会自动触发的保证。

原始轨迹记录的累计输入 / 缓存输入 / 输出 token 分别为：
基线 `290308 / 264576 / 4482`，候选 `411785 / 376704 / 10271`。
这是整个运行跨调用的累计量，包含重复及缓存输入；候选还选择了不同的验证步骤，
单组数据不能用于归因插件开销、推断稳定成功率或宣称节省成本。

本机沙箱首次阻止 app-server 启动；经命令权限批准后两边均完成。
试运行中宿主的子审阅线程曾遇到 `no rollout found`，不记作 CodeStack 的行为缺陷或审阅通过。
本轮开发另有独立审阅，结果如下。

## 5. 独立 Review 与剩余边界

两项独立审阅分别检查规则语义/适配和测试/包/评测边界。
审阅为指令约束的只读模式，不声称操作系统强制隔离。
已修复并复验两项发现：

1. 将“注解或注释变更均可跳过持久化规则”收窄为“仅文档注释变更”。
   持久化注解可能改变加载、映射和生命周期，即使没有方法体变更也要选择相关规则。
2. 修复 SQL 检查器遗漏 CTE 等 SQL 形态的问题，按实际执行计数。

修复后本次实现范围没有遗留的已确认实质问题。仍需保留以下证据边界：

- P5 没有完成计划中的三个代表场景各条件 3 次及全部 R01—R19 的原生行为矩阵。
  当前只有 R02 的 1 对试运行；其余场景有输入和判定要求，不能记作宿主通过。
- Claude、ZCode 原生加载、隐式调用及行为未验收；Codex 插件安装/升级也未验收。
  `product.json` 的 hosts 表示构建目标，不表示真实行为已通过。
- JPA/MyBatis 规则经过源码和独立语义审阅，匿名上下文不提供真实 ORM 执行证据。
- 发行材料、release.json、Actions plugin choices 按批准计划留待后续接入。

用户当前授权止于实现、验证和 Review。所有改动保留未提交；未执行 commit、push、
tag、PR、发布、正式市场同步或宿主安装。

## 6. 本地证据定位

以下临时路径只作本次复核线索，可能被系统清理，不作为可分发资源：

- 统一门禁：`/private/tmp/codestack-suite-20261018.log`。
- 定向契约与 lint：`/private/tmp/codestack-contracts-20261018.log`、`/private/tmp/codestack-lint-20261018.log`。
- 最终构建及索引：`/private/tmp/codestack-final-jyjuvw7i/packages/`。
- SQL 回归反例与正向控制：`/private/tmp/codestack-sql-calibration-48vZXF/`。
- 主智能体独立 SQL 复验：`/private/tmp/codestack-h2-final-8wuvr7af/results.json`。
- 原生试运行：`/private/tmp/codestack-native-athhmr9n/{baseline-1,candidate-1}/`。
- 独立行为检查：`/private/tmp/codestack-oracle-final-lc3lo6bv/results.json`。

两份原生 events.jsonl 的 SHA-256：

```text
baseline:  65514ccb40e9b9729fed60b21d151e94691e657c7ab75dc4a8029ac9b4051578
candidate: 23c3c02816992077214a88af7840262d0a801a2f1874ad96cc977b0b7723d244
```

原始宿主日志、配置内容、数据库驱动和私有材料不复制进源码或发行包。
