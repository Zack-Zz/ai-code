# CodeStack 边界修复与行为复核

日期：2026-10-18（Asia/Shanghai）。本记录承接首轮实现后的全面 Review。
状态：四点修复、本地验证及独立复核完成，等待用户 Review。

本文件保留上一轮状态；后续新增规则及当前资源证据见
[复用、抽取与嵌套类型交付](2026-10-18-codestack-reuse-and-nesting.md)，下文哈希不代替该轮验证。
用户已批准修复四点、同步中文设计和中英文说明、补充反例及行为验证；
不包含 commit、push、tag、PR、安装、发布或正式市场同步。

## 1. 修复范围

| Review 问题 | 本轮结果 |
| --- | --- |
| 空 ID 一律空响应，覆盖正常结果契约 | 必需正向包含集合为空时不查库并返回空；排除集合和项目明确允许的可选筛选保留原语义；所有分支保留租户、权限和数量边界 |
| 所有 XML 都要求 MyBatis 规则 | 仅确认的 MyBatis Mapper XML 读取对应规则；JPA XML 按实际机制选择；其他 XML 不从扩展名推断持久化；无关 Java/Javadoc 不修改 |
| 已授权分批导出仍可能重复确认 | 复用已有范围、批次、预算、终止及一致性约定；局部变更不另加审批；缺失决定影响任务或扩大已授权范围、预算时才处理相应澄清或同意 |
| README 增加插件后仍有旧信息 | 同步根及插件双语 README、双语开发和安装指南；三个插件独立；CodeStack 无额外运行时且尚未进入正式市场；CodeVow 1.0.4 来源明确为仓库发行记录和三宿主清单 |

执行内容保持英文，中文规则稿和插件设计稿已同步。没有增加运行时、技术栈分类器、
Hook、独立 Agent、业务项目配置或插件依赖。初始开发版本仍为 `0.1.0-preview.1`。

## 2. 对应反例与检查器

新增 [R20—R24](../../plugins/ai-code-stack-standards/evals/cases.md) 和三个匿名项目：

| 场景 | 冻结判定 |
| --- | --- |
| R20—R22：必需包含、排除、明确可选筛选的空 ID | 在真实 H2 中分别验证 0、1、1 次 SQL，完整比较结果；再检查非空筛选、租户、倒序、offset、分页及输入上限 |
| R23：仅修改 JPA orm.xml 列映射 | 标准库解析 XML 并比较结构；其余 seed 文件逐字节不变；实际引用读取由原生轨迹判断，不从 XML 输出猜测 |
| R24：已批准导出局部追加 status | 170 行和 200 行结果均实际执行 4 次 SQL，每批至多 50 行；检查混合状态、租户、范围、顺序与上限；是否重问审批另读实际对话 |

项目 seed 进入临时工作区；case catalog、检查器、oracle 和操作员判定留在外部。
候选新增或篡改规则不能构成通过，独立核对 staged Skill 字节和允许修改范围。
JPA XML 检查不执行 ORM，也不声称验证了 provider；H2 证据只对应匿名 JDBC 输入。

最终校准 **14 项**：3 个手工正向控制退出 0，11 个错误控制以预定语义断言退出 1。
反例包括错误空响应、空包含仍查库、丢失 offset、把 JPA 文档改成 MyBatis、
修改无关 Java、放大导出批次，以及硬编码状态。
这些结果用于证明检查器能区分相应产物，不是模型成功率。

### 本轮额外发现并修复的验证缺口

独立审阅发现初版导出 oracle 的授权行均为 ACTIVE，硬编码 ACTIVE 也会通过。
先加入“硬编码应被拒绝”的控制：旧 oracle 实际退出 0，校准外层断言退出 1，构成有效 RED。
随后使用 ACTIVE、INACTIVE、PENDING 混合数据；同一错误产物退出 1，正确取列值的产物退出 0。
该修复在 R24 原生运行开始前冻结，未根据候选输出临时放宽检查。

最终冻结检查器哈希：

| 文件 | SHA-256 |
| --- | --- |
| check.py | `55dc579e0b23e2e6468da64c30a12ba84ccd80e3b9316786ee238c31a64fe2ea` |
| EmptyFilterCheck.java | `d26aed9bd776ddd69ba9dd448e5983cae868fbb6e14d32b9937d092617ddddda` |
| ExportCheck.java | `6d8603c9a9ad1b1fff5d9809853149c895005404e8c5ff6a9df4f59e0e8200e2` |

## 3. 原生行为对照

使用 Codex CLI `0.163.0`，沿用本轮用户配置的 `gpt-6.1-sol`、`ultra`，没有手动换模型或档位。
这与首轮 R02 的模型不同，不能跨轮合并为同条件对照。

本轮每个项目运行修复前、修复后各 1 次，共 3 个任务、6 次运行。
R20—R22 是同一次复合任务中的三个判断，不是三个独立模型样本。
对照条件是旧 CodeStack 与修复后的 CodeStack，**不是启用与未启用插件**。
同一对使用相同起始文件、普通中文任务、当前模型配置和已有 CodeVow 环境；
提示词不点名插件或规则。配置若在运行中改变，脚本会停止后续配对。

临时工作区仅放源码 Skill 副本，不进行原生插件安装。过程参考
[OpenAI Docs 的 Skill 评测说明](https://developers.openai.com/blog/eval-skills)，
分别检查轨迹、实际修改和独立结果，不能以模型口头声明替代读取证据。

六次运行均退出 0，随后使用同一冻结外部判定器重新编译、检查，六次也均退出 0。
以下引用读取来自已完成工具命令的实际内容；审批行为另逐条核对对话，没有用关键词分类器替代模型行为。

| 任务 | 修复前实际读取 | 修复后实际读取 | 独立结果与范围 |
| --- | --- | --- | --- |
| R20—R22 | Skill、Java、数据访问 | Skill、Java、数据访问 | 两边三种空集合语义和 SQL 次数都正确；仅改 UserDirectory.java |
| R23 | Skill、JPA、数据访问 | Skill、JPA | 两边仅改 orm.xml 的目标列；其余文件和 Java 字节不变；均未读取 MyBatis 或 Java 规则 |
| R24 | Skill、Java、数据访问 | Skill、Java、数据访问 | 两边混合状态及 170/200 行检查通过，均为 4 次 SQL；没有重复请求批准，仅改 TenantExport.java |

六次暂存 Skill 的完整文件集和字节均保持不变，项目中没有其他新增文件或无关改动。
**旧版在这些任务中也已经正确，没有复现此次评审指出的误用，不能据此声称效果改善。**
本轮确认修复后的规则在这些局部普通任务中被自动选用、结果和修改范围符合预期；
单次配对不建立稳定成功率。原有语义冲突通过规则审阅消除，不能把手工错误控制伪装为模型 RED。

宿主保留了原有实验特性告警；候选运行中独立审阅工具也曾不可用，该环节不记作审阅通过。
候选自述的覆盖率不作为本轮外部验证结论；本实现另由主任务的独立审阅检查。

## 4. 本地技术验证

| 检查 | 本轮结果 |
| --- | --- |
| `python3 -B tooling/plugin_tool.py validate --all` | 退出 0 |
| `PYTHONDONTWRITEBYTECODE=1 npm test` | 退出 0，6 个测试组通过，CodeStack 9 项契约通过 |
| `npm run lint` | 退出 0，最终文档状态复验通过 |
| `python3 .github/scripts/check_no_dist.py --root .` | 退出 0 |
| CodeStack 三宿主 build 与逐包独立 package check | 全部退出 0 |
| 外部行为判定器 14 项校准 | 全部符合预期 |

最终运行资源源码哈希：

```text
184b0c24e0dbe8dc069d905e2534c84083fb7f1aff1d08a6011ea148cc3fc742
```

| 宿主 | package_content_hash |
| --- | --- |
| Claude | `9b03f5e48be53ca61f1e19dc566eb42b5ad8005c4ba34f60e6a39162d7fa751a` |
| Codex | `cf5f5576273ce5127a2e5294fc5ecb6adab11afb490d41517eb9f326c1bba6d9` |
| ZCode | `d5e6e1187dcb7dc9f7dd0337e425e1fc9e244ee0a11de072afadc1dc9b71c882` |

构建基准 HEAD 为 `a62b7b42461ffda5fd6168a6197f060492760877`，工作树未提交。
本轮资源哈希与首轮不同，首轮构建和原生记录只保留为历史证据，不能代替本轮通过。
评测工具、测试及维护文档不进入资源白名单和三个宿主执行包。

## 5. Review 与证据边界

独立 Review 已检查四点规则和说明同步、新增 oracle，并发现和复验修复了状态恒值缺口。
审阅约束为 `policy_only`，不声称有操作系统级写入隔离。
最终六次轨迹、修改范围、冻结判定器、源码/包/轨迹哈希及报告均已独立复核，
未发现本轮范围内尚未处理的可操作问题。

原生副本发现不等于插件清单加载或安装/升级验收。Claude、ZCode 原生行为、
完整路由矩阵及原计划重复次数保持 pending；不以本轮局部样本宣称稳定触发率、
编码效果改善或成本收益。后续发行配置和正式发布仍属于独立步骤。

## 6. 本轮本地证据

工作目录：`/private/tmp/codestack-boundary-review-u2ow2n8v/`。
其中 `suite.log`、`lint.log`、`packages/index.json`、`status-red.log`、
`calibration/calibration.json`、`evaluator-files.json`、`runs.json`、
`native-results.json`、`independent-grades.json` 记录对应检查。每个 `runs/<case>-<condition>/` 保存原始轨迹、
最后输出和产物。临时文件可能被清理；原始宿主日志、凭据和驱动不复制进源码或发行包。

| 原生轨迹 | events.jsonl SHA-256 |
| --- | --- |
| R20—R22 修复前 | `18e64dc4c8703fe74f71354d529bc177c26e2fb160cf03636eddaa75f32adb3b` |
| R20—R22 修复后 | `d854cc1fda54a999553dc03ddbf6e87762f5f31518571ee8734dfae5841a008c` |
| R23 修复前 | `500c48ebad9299f9019a168f6d2e48919263e837514a50a0865b25a5356d3969` |
| R23 修复后 | `4b2f51c9dfab410b562ac2c8ef7513e80adea0ccbfb7317b3e930f55f4af9c24` |
| R24 修复前 | `07924cf24a4c55d00dfd603aaf4bfa2e60149bfe3f625278f5a09caadad852d7` |
| R24 修复后 | `c45bfecbf62dd2ce1fd180f825b4f7dcdb4e27f80240ded613ec72945e98595d` |
