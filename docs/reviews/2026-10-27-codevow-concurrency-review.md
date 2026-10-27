# CodeVow 并发论证与保护职责：实现、验证与 Review

日期：2026-10-27（Asia/Shanghai）。基线为 `fc2afe2`；本记录覆盖后续未提交的
版本规范、候选版本更正，以及本轮两条设计与 Review 规则。用户已明确授权在
验证和 Review 无问题后提交、推送全部本次项目改动；未授权发布或安装。

## 最终规则与范围

1. 设计和 Review 的并发问题须说明可达链路：请求、任务或实例，相关共享状态，
   执行顺序与违反的业务约束。源码和执行模型可以作证，无须生产事故；缺失
   关键事实时列为待确认假设，不能包装成确认缺陷。
2. 每个新增保护机制须有明确职责。核对已有约束、事务和条件更新的覆盖，解释
   新锁、重试、补偿或恢复解决的问题，权衡正确性、可靠性与维护成本。允许
   必要复杂度，也审查重复保护及只有未证实场景支撑的防御逻辑。

没有加入禁止多实例、默认单实例或按最少代码选择方案的规则。没有增加配置
开关、运行时协调器或新的评分器。

- 规划入口：[execution.md](../../plugins/codevow/skills/workflow/references/execution.md)。
- Review 入口：[review/SKILL.md](../../plugins/codevow/skills/review/SKILL.md)。
- 跨宿主 Reviewer：[共享合同](../../plugins/codevow/skills/review/references/reviewer-contract.md)。
- 双语使用说明、Reviewer 描述和 CodeVow `1.0.6` 的候选说明同步更新。
- 保留同一轮未发布候选：CodeVow `1.0.6`、CodeStack `1.0.0`。新插件从
  `1.0.0` 起步、后续默认补丁位加 1；已有 `0.x` 发布历史保留，用户明确指定
  版本或升级级别时按该要求执行。

## 验证素材与 TDD

新增 A37–A39，共用匿名 SQLite 标准库样例，进入已有 prepare/collect/grade
流程。A01–A36 的案例对象逐项比较未变；评估素材不进入公开插件包。

- A37：两个独立连接都可能查不到同一键，唯一约束和事务仍维护同一登记 ID、
  首个 payload、单条 outbox，以及租户隔离。
- A38：旧原子计数更新得到 12；候选读后写的确定性交错得到 11，违反两个成功
  请求各加一次的要求。没有 sleep、随机竞态或外部服务。
- A39：审查租约、事务重试、发件箱恢复及补偿的职责。给定接收方提交后超时，
  重试耗尽再删除本地登记与意图，违反已给持久要求；接收方幂等契约、租约
  时长、争用收益和未实现的 claim 设计保留为待确认事实。

新增三项 Python 测试先因缺失 A37–A39 返回 `unknown case_id`，形成有效 RED；
添加案例和准备器接线后 GREEN。它们验证逐字节复制、基线与材料绑定、真实
SQL 结果、篡改拒绝，以及无真实 Agent 轨迹时仍为 `not_run`。既有 evals 50 项
定向回归通过。

集成时旧 Node 目录契约因只接受 A01–A36 有效失败；更新为 A01–A39、第八份
fixture 和明确的关键案例集合后通过。未增加只匹配新指令措辞的测试。

提交前暂存检查发现差异素材中的空白上下文行触发 Git 尾随空白检查。改由两版
源码生成无上下文 unified diff，临时副本实际应用后与候选源码逐字节一致；
受影响的三项评估保护测试重新通过。该展示格式更正不改变两版源码或评分预期。

## 独立 Review 与前向演练

一个 code_implementer 负责评估素材与准备器测试；主代理负责技能、共享合同、
适配描述、使用说明、版本规范整合、实际包检查及 Git 交付。

独立 code_reviewer 在未读取评分预期、exercise.py 或测试答案前，依据原始
需求、源码、差异和方案完成三个请求的前向分析：认可已有数据库保证，推导
出 10/10→11/11 的丢更新，识别删除补偿的持久性问题，同时保留必要恢复设计
并区分开放问题。随后读取评估接线及测试，完成最终 diff 与实际包审查。

独立 Review 结果：阻塞 0、应修复 0。Reviewer 为 `policy_only` 指令层只读，
没有修改文件或自行执行测试、外部调用。主代理完成集成自审和验证。

## 最终检查

| 检查 | 结果 |
| --- | --- |
| 统一 `PYTHONDONTWRITEBYTECODE=1 npm test` | 6 组通过；公共 Python 345、CodeVow Python 330、Agent Delegation Python 35，另含 Node 组 |
| 新评估与既有 evals 定向测试 | 3 + 50 项通过；差异素材展示格式更正后，受影响的 3 项再次通过 |
| 全部宿主构建与逐包可信源检查 | 11 包通过 |
| 两候选 draft prepare/verify 与 historical | 通过；CodeVow 331 文件，CodeStack 139 文件，schema 3 |
| 四端共同规则及生成 Reviewer | 与源码逐字节一致；Claude/ZCode 各嵌入一次，DSH persona 解码等于合同全文，Codex 引用可达 |
| DSH 官方 RC2 隔离 API 组合 | 16 项通过，包含真实 Loader 激活及预设挂载 |
| validate、Lint、维护技能、diff、dist 与市场快照检查 | 通过；公开快照未修改，无 pending distribution |

实际包与报告位于 `/private/tmp/ai-code-concurrency-final-pzqcd9hv/`。共享合同
SHA256 为 `730c72878f106c174dc36d4a24ec6dd92d8d54b53e6edf1061f2f3af38a107f7`，
其余规划与 Review 哈希见 `report.json`。全量门禁日志为
`/private/tmp/ai-code-concurrency-final-suite.log`；原生 API 日志为
`/private/tmp/ai-code-concurrency-native.log`；目录契约 RED/GREEN 日志为
`/private/tmp/ai-code-concurrency-catalog-red.log`、
`/private/tmp/ai-code-concurrency-catalog-green.log`。

前向演练仅证明本地独立 Agent 对这三份材料的推理结果，不代表各真实宿主的
自动选择、安装或实际会话验收。DSH API 组合使用真实 Loader 与合成 Agent，
没有模型会话、用户 profile 或真实文件工具执行。四端 acceptance 保持 null，
publication_ready=false；本轮不执行发布、市场部署或用户安装。
