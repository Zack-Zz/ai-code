# Agent Delegation 候选实现与验证记录

日期：2026-10-08。公共发布基线：`main@b2a500a`；本插件与相关新增文档
保留当时的未提交状态。设计与前期验收阶段没有 Git、安装或公开发布授权；
2026-10-09 用户已另行授权开发完成、review通过后commit/push。历史测试
仍绑定各轮源码/包字节，新的Git授权不构成安装或正式release验收。

## 已落地范围与责任

`plugins/ai-agent-delegation` 0.1.0 已登记 catalog，拥有独立 product、单一
agent-delegation 技能、三宿主元数据、白名单、Python 标准库薄 CLI client、
33 项测试、支持矩阵和 release 候选资料。

只在当前用户明确交给 Claude Code/ZCode/Codex 或同工具另一个独立会话时
派发。普通实现、架构、审阅、原生 subagent、引用指令和模型 approved 标记
不自动切换流程。Source/current-user、scopeReference 和 receipt 只记录
约束来源，不被宣称为人类身份认证。

执行、进程、任务、工作区、持久化和 CLI/MCP/API 属于 ai-mcp 的
`@ai-mcp/agent-bridge`。本插件消费该外置 CLI，组织交接与回收，不复制
驱动/任务服务，不管理模型、账号或强制开发审阅流水线。Codex 发布 profile
仍为 skills-only，未在任何宿主插件包声明原生 MCP 运行支持。

## 多插件发布会话的衔接

会话「讲解插件发布机制原理」已提交公共分发机制 `b2a500a` 并通过远端 CI。
本轮读取其范围但没有向它发送消息；未修改发布/市场部署生产工具或已提交
CodeVow 行为。新插件沿用独立身份、版本、资源闭包、制品和发布契约。

新增第二插件后，统一测试暴露公共 distribution subset 测试只更新
ai-code-workflow 的假设。已按真实失败修正为遍历所有 index.plugins：这是
测试 fixture 对多插件输入的修复，未放宽校验器或公共发行门禁。

两插件三宿主构建与六个可信源码包检查通过，根 npm test 的 5 组统一门禁
通过。认证控制面补验阶段的派发 source_tree_hash 为 `b17748ca064786bb9115d00e795b4a8865e5acabbc255a72ca7dbdedaf330056`；
CodeVow source_tree_hash 保持 `24793827cd6d0c2d2e890a12f671575afd1cf9ba5b1a68d7f4355e0b711e6ae9`。
公共根 market/dist 已按新注册成员生成，marketplace sync --check 与 check_dist 均通过。

薄 client 子进程 fixture 证明无 shell 拼接、严格 engine/TaskSpec、真实意图
门控、同引擎 flag、精确 task/session/receipt、错误确定性与临时输入清理。
它不等于原生模型或宿主已支持；所有 release acceptance 仍为 null。

## 真实 Claude Code 宿主证据

脱敏原始材料保留在
[/private/tmp/agent-delegation-host-ily58rpu/REPORT.md](/private/tmp/agent-delegation-host-ily58rpu/REPORT.md)，
绑定当时源树哈希 `7ce38aba79370c378430dce73f6ec941302eae6803a35834d4d4203d07860693`。随后薄客户端修正 existing 的 preflight/start 策略一致性，当前包哈希已变更；旧宿主证据不自动转为新包验收。临时 public build + trusted package check 后用原生
`--plugin-dir` 加载，未持久安装，不拷技能正文进 prompt。Claude 2.1.177
实际默认模型为 deepseek-v4-pro[1m]，未替换认证/Provider/模型。

| 场景               | 实际观察                                                                           | 结论                                     |
| ------------------ | ---------------------------------------------------------------------------------- | ---------------------------------------- |
| 自然语言明确派发   | Skill `ai-agent-delegation:agent-delegation` 自然被选择                            | 原生加载和自动触发已观察；完整派发未通过 |
| 架构讨论负例       | 正常终态、零 Skill 派发/Bridge/目标执行、临时代码未变                              | 此场景通过                               |
| 引用派发负例       | 只总结引用，正常终态、零 start/continue/目标执行                                   | 此场景通过                               |
| 完整正例           | 原生 Bash 初始化 `~/.claude/session-env/<SID>` 外层 EPERM，60s 中止；未调用 Bridge | 未完成；不能用 Skill 触发代替派发闭环    |
| 读取型普通开发负例 | 相同 session-env EPERM 导致有界超时；零 Bridge                                     | 仅零派发观察，不能算完整通过             |

模型要求的 dangerouslyDisableSandbox 未授权/未执行；尝试敏感全局 probe
被原生权限拒绝，确认该文件不存在。测试没有绕过原生权限，也没有启动
第二个付费原生目标（目标原为固定 fixture engine）。

补跑完整正例的外层提权被自动审批拒绝。原理由为：真实 Claude Code 使用
默认认证可能向未明确授权的模型服务发送插件/虚拟项目内容，并写入用户级
原生会话状态，缺少针对该具体调用和数据外发的授权。拒绝后未重试绕过；
主会话当时询问用户是否允许本次限定验收。2026-10-09 的澄清、重新审批
与后续证据见下节，旧拒绝不再被列为当前等待项。

## 2026-10-09 当前模型原则与补充验收

用户明确 Claude Code、ZCode 使用当前可用官方或第三方模型均可，插件与
Bridge 不设置模型白名单或固定模型分工。两仓架构与设计已同步此原则。

该阶段源树 b17748ca… 的 Claude 2.1.177 默认 deepseek-v4-pro[1m] 正例已
完成自然加载、真实 CLI preflight/start/get/产物读取、准确 task/session
与登记验证；目标为受控 fixture。普通开发、架构讨论、引用指令三个负例
均正常完成且零派发。Bridge 沙箱禁查进程的客户端缺陷已修复为认证 IPC，
runtime 的启动/恢复/取消进程校验保留；本地全仓 557 项与原覆盖阈值通过。

Codex bundled 0.162.0-alpha.2 通过 native selectedCapabilityRoots 载入完整
候选，自然识别技能并使用包内薄 client；三个负例均 completed/零派发。
正例 fixture 任务 completed、回执与 6 个产物一致；发起端被验证预算中断，
最终用户报告未完成。原 caller 为 ephemeral，准确 resume 返回 no rollout，
未以新 session 冒称恢复。未安装、修改全局配置或填写 release acceptance。

证据分别在 `/private/tmp/agent-delegation-host-model-policy-20261009-_b3126dy`、
`/private/tmp/agent-delegation-claude-negatives-20261009-c_tymomf`、
`/private/tmp/agent-delegation-codex-native-20261009-ysdxq_f1`。
[Bridge 当日记录](../../../ai-mcp/docs/reviews/2026-10-09-model-policy-and-cli-validation.md)
同步记录 ZCode 当前既有 GLM profile 的适配，区分真实原生结果与 fixture。

## 尚未完成

- Codex→真实 Claude、Claude→真实 Codex 完整正例均已在54b新包补验。
  前者保留原生 TMPDIR 验证偏差，后者新轮原件保留/isolated且没有混合候选。
  ZCode 宿主正负闭环、
  三端完整场景矩阵及同引擎独立 session 的宿主场景仍未完成。
  三端原生安装/更新和发布 acceptance 未完成，矩阵保持 unverified。
- ZCode 当前 standalone CLI 账户路径不支持桌面 start-plan JWT/Bearer，
  individual 索引也缺失。前次 API-key 转换语义不匹配，签名失败不能证明
  桌面凭据失效；成功 session 待实际入口。不伪造授权或以模型品牌作门禁。
- [Bridge 技术实现记录](../../../ai-mcp/docs/reviews/2026-10-08-agent-bridge-implementation.md)
  单独报告三驱动实际能力，尤其 Codex read-only apply_patch 写入后的明确拒绝。
- 当前新增插件未提交或发行；正式公开发行另走本插件 tag、字节绑定验收与
  公共发布 workflow。其他会话的 CodeVow Release 授权不扩展到本插件。

编译后 Bridge 与本薄客户端的真实进程联调通过（fixture目标）：稳定task/session、receipt刷新、重复requestId零额外启动、原项目保留；独立服务最终显式停止。当前六包可信检查、统一5组门禁、根lint、市场/dist一致性通过。CodeVow只有生成元数据 source_revision 随已完成公共提交从92ee584更新为b2a500a，源码/资源哈希未变。

## 2026-10-09 stdin 新候选与真实目标

真实 Codex 发起端暴露默认薄客户端在源码 cwd 内暂存 spec、触发 DIRTY_SOURCE
的缺陷。有效 RED 后将 spec/message 改为 subprocess stdin；Bridge CLI 的
`--spec-file -` / `--message-file -` 接收有界 UTF-8，保留严格契约和错误语义。
没有 shell 拼接、控制临时文件或失败后替换 request/session 的自动重试。

当前 source_tree_hash 为
`54b06e1e156e4846719de18a41a1d748bdab9e43afc1bfd6c8f36a690e54713d`，
Claude/Codex/ZCode 包 content hash 分别为 e71ad4d2…、93472c38…、5fa8dad0…。
插件 33 项、Bridge 全仓 66 files / 565 tests、原80%覆盖门禁和统一5组测试通过。
两插件6包可信检查、根市场只读一致性检查与 check_dist 通过；CodeVow 源树
仍为 24793827…，未改变其行为。构建产物仍为本地未提交候选。

新 Codex 包通过原生 selectedCapabilityRoots 自然加载，实际默认模型
gpt-6-astra/openai。16 次控制调用保持源码项目 cwd，spec 通过 stdin；
任务 `task_ec808a52-9a42-43fb-898b-8a78fa0c570e` completed、仅一轮，真实
Claude 2.1.177 / glm-5.3 的 session 为 `198090af-d875-4925-b1eb-14baca905afe`。
独立 Node 验证从 baseline exit 1 到交付 exit 0；原件 ZERO、隔离交付 ONE，
单个换行和写入范围符合要求；6 产物哈希一致，发起端正常完成最终报告。

证据保留在 `/private/tmp/agent-delegation-codex-stdin-native-20261009-q6lowe45/REPORT.md`。
验证脚本将原生父进程 TMPDIR 指到源码项目，原生工具产生 node-compile-cache；
未删除该未跟踪缓存，不把 Bridge 零控制输入临时文件推广为零原生缓存写入。
原生 CLI 和临时 capability root 加载不证明桌面市场安装/更新。

另有 Claude→真实 Codex 目标 completed、existing 工作区验证通过，准确
caller resume 后只读回收并正常报告；未重建目标。首次绑定旧候选、收尾
加载新候选，按阶段记录。详见
[Bridge 跨工具补验](../../../ai-mcp/docs/reviews/2026-10-09-native-cross-agent-and-stdin.md)。
模型沿用当时可用配置，不设置官方/第三方品牌门禁；部分成功不填写完整
三宿主正式 release acceptance。

真实 Codex 同工具独立会话的准确绑定与上下文续接另有观察，但 native
leader 退出后仍残留同组 Git 网络进程，Bridge 清理后保持 failed/unknown。
该场景未标为通过；限定独立只读审阅没有确认 Bridge P0/P1/P2 缺陷，
不以该结论替代三宿主完整验收。

新54b/e71ad Claude→真实 Codex 独立正例已另取完整证据：caller
d75c74a0…/glm-5.3[1m]，task_f3e594b1…、target session01a11efb…/gpt-6-astra，
单 run completed，原件ZERO/isolated ONE，Node RED→GREEN，六产物哈希与
回执匹配，caller 正常完成最终报告；没有关闭原生功能、覆盖TMPDIR或混合包。
证据在 `/private/tmp/agent-delegation-claude-to-app-codex-54b-20261009-4qsq3hu8/REPORT.md`。
上述仍绑定当时 b010ff81… CLI，后续 Bridge app-server 默认适配的 native
整链验证单独记录。ZCode 认证及实际 Codex MCP 旧协议拒绝见
[原生协议与账户补充](../../../ai-mcp/docs/reviews/2026-10-09-native-protocol-and-account-path.md)。

## 2026-10-09 开发与Git交付收口

功能源码已覆盖明确派发门控、保留目标、同工具独立会话、交接、stdin
消费、回执和产物回收，没有把普通开发改为默认跨工具派发。ZCode的
公开CLI适配已由Bridge实现；当前standalone不支持桌面start-plan账户
路径，未发现遗漏的公开会话参数，不在插件中制造认证或模型管理。

支持矩阵现在明确区分部分真实场景与整包未完成的正式验收，三个release
acceptance仍为null。这次文档变更会改变候选source hash，旧54b记录
保留为历史，不据旧包填写新包验收。最终包与统一工程门禁在Git提交前
重新构建、校验；CodeVow源码及资源保持原样。

Bridge默认app-server与启动前持久化停止证明要求的收口，以及原生
新建/准确续接/取消的环境绑定限制见
[开发交付记录](../../../ai-mcp/docs/reviews/2026-10-09-agent-bridge-development-delivery.md)。
本轮没有tag、PR、宿主安装或公开发行授权；Git结果以最终回执为准。

独立review还确认了同一路径receipt并发覆盖的P2。两个真实Python进程
同步发布点的有效RED为两者均写成功、前任务绑定被覆盖；修复后跨进程
互斥覆盖检查与发布全过程，繁忙或不同绑定返回明确失败并保留原绑定。
进程退出由内核释放锁，不按PID清理锁文件。插件35项测试通过，包括
同绑定幂等、null→准确session补录和锁持有者退出后的再次写入。

独立code_reviewer（GPT-6.1 Sol/max，指令限制只读）已复审上述修复及
Bridge的停止证明持久化；当前审阅范围无确认P0/P1/P2遗留。其反例使用
内存替身，真实双进程竞争由主会话执行，不能互相冒称。CodeVow三端旧包
除artifact.json的source_revision外，技能、工具及其他资源字节保持一致。

最终源码source_tree_hash为
`69b69870234f86c9d8e45e0e3b3a7ae0a932ab8cecfe62d07ff52e4bd2b6214c`。
三宿主content hash分别为3d897aee…、0a2ae3ca…、02654b71…；两插件六包
可信检查、5组统一门禁、lint、validate --all、marketplace sync --check及
check_dist均通过。CodeVow source hash继续为24793827…，本轮生成制品
的source_revision更新到公共HEAD d020da1，不修改CodeVow发行或preview市场。
这些是本地候选工程与包完整性结果，三个正式release acceptance保持null。
