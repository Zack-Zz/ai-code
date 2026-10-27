# AI 工作流首版完整开发 Prompt

迁移说明（2026-10-07）：本文件保留首版设计基线，源码路径现相对
`plugins/ai-code-workflow/`。仓库级目录注册、通用清单元数据、独立插件版本
和 schema_version=2 发行索引以
[多插件规格](../../../../docs/design/2026-10-07-multi-plugin-design.md) 为准；
原 workflow 行为与任务/证据契约仍由本插件维护。历史执行 Prompt 不构成
当前授权，历史验证结果不因迁移获得新的通过声明。

请在 `/Users/zhouze/Documents/git-projects/ai-code` 完成 AI Code Workflow 首版的全部开发工作。保留当前仓库身份，面向公开产品，首发适配 ZCode 与 Codex，Claude Code 后续接入。

## 设计来源与总体授权

先完整阅读以下四份文件，它们共同构成本轮实现规格：

1. `docs/design/2026-10-01-workflow-v1-task-design.md`
2. `docs/design/2026-10-01-workflow-v1-implementation-spec.md`
3. `docs/design/2026-10-01-workflow-v1-data-contracts.md`
4. `docs/design/2026-10-01-workflow-v1-acceptance.md`

本 Prompt 即为上述设计和 B0 至 B7 总体开发计划的确认。先输出实际文件级执行清单，再直接按依赖顺序实施；既定范围内的普通实现细节不需要逐任务重复确认。技术选择、字段、命令、路径和完成条件以实现规格及数据契约为准，任务总览不覆盖它们。

实质性范围变化、用户数据风险或未授权外部操作需要处理，但先完成所有不受影响的工作。不能只写文档、测试壳、空目录、TODO 或返回开发建议就结束。

允许修改本仓库内实现所需文件，在 `/private/tmp` 创建恢复快照、一次性 fixture 和隔离验证目录；允许在项目内安装必要维护/测试依赖，使用项目内或临时缓存，不安装到用户全局。管理工具保持 Python 标准库实现，不为便利引入新 Agent 运行时或服务。

允许按需要使用至多两个并行、范围独立的子任务或只读 Reviewer，继承现有模型，不自动降级、不嵌套派发。Reviewer 只报告发现，主执行者核实并修复。实际宿主没有相应权限控制时，如实说明限制。

## 执行边界

不对本仓库执行 commit、amend、tag、push、merge 或创建 PR，不发布 npm/GitHub/插件市场版本，不创建新的产品仓库。工作区已经有大量已确认删除和未跟踪素材，不要求恢复成干净 Git 状态，不 reset/clean/checkout 丢弃它们。

不修改普通使用的 `~/.codex`、`~/.zcode`、模型、权限、MCP、其他业务仓库或现有插件集合；不修补应用目录，不自动重启桌面应用或关闭其他聊天。

允许在明确的隔离测试工作区/profile 内使用现有已登录官方客户端，创建仅服务本轮验收的新会话并发送验收定义的测试输入。原生安装只在这个已授权隔离环境进行，不能用自有脚本硬写宿主内部注册或缓存。无法安全隔离或需要用户完成登录/重启时记录具体阻塞，不把它当作全部本地工作停止的理由。

A18/A19 的专用临时 Git fixture 可以 git init，并在该临时仓库进行场景明确授权的本地 commit；此许可不适用于产品源码仓库，也不包含 push/tag/merge/PR 或任何生产远端操作。测试会话使用独立输入，不将本完整开发 Prompt 的总体授权误注入需要测试未确认状态的场景。

## B0 固化基线

读取实际 AGENTS、git status、diff 和所有剩余文件，建立本轮开始状态。将已有修改和本轮可能迁移的未跟踪来源保存为仓库外可恢复副本，记录哈希和路径。

复跑 npm test、tests/run-suite.test.js 和 git diff --check。既有清理快照中 review-results 测试的 1 项哈希漂移已在收尾记录说明，不能修改旧 SHA256SUMS 使它看起来完全一致；核实实际副本和已授权变化，并保存本轮新基线。

清理收尾的已知缺口是 npm test 尚未注册汇总器自身的 5 个测试，且自定义空组列表会被判为成功。先将自身测试纳入默认门禁，为空集合补有效失败测试并修正判定，验证默认命令实际运行所有现有测试组，并复核清理后的入口、保留资产和引用。发现确定的收尾问题先修复，再进入 B1；不要把分别运行成功当作默认门禁已经完整。

后续 diff Review 区分此前 525 项删除、已有修改和本轮新增/修改，不能只看相对旧 HEAD 的巨量删除。新增未跟踪文件也要读取和审查，不能认为 git diff 没有显示就没有改动。

## B1 协作契约与数据工具

按规格建立 product.json，产品 ID 为 ai-code-workflow，展示名 AI Code Workflow，未发布候选版本 2.0.0；根 Node 包仍为 ai-code、private=true，版本统一。

实现两份策略、四份固定 schema、product/policy/io 模块及受控 CLI 基础。默认 collaborative，continuous 不能制造授权；解析项目覆盖和用户显式选项，记录逐字段来源与策略 hash。

覆盖重复/未知字段、非法类型、bool 冒充 int、非法模式、资源越界、源缺失和重名。资源使用确切文件白名单，不递归打包同目录里的未知文件。全部行为工具先定义有意义的失败测试，再最小实现和复验。

## B2 核心技能和验收输入

提炼 workflow、tdd、debugging、review、verification 的共享源码，每项明确输入、触发、职责、失败和交付条件。保留 review-results 的单一呈现契约，review 调用它，补新入口委托与资源解析检查。

统一 QUICK、紧急任务和已有授权的处理，消除 BEL 正文、个人全局规则与旧验收表之间的冲突。核心不依赖个人文件、不绑定语言框架、具体模型或某宿主工具名称，不恢复旧教程库和机械代理流水线。

同步实现 cases.json 中 A01 至 A25 的具体输入、fixture、checks、required_evidence 和 critical 字段，准备规格要求的 Python、JS、恢复、Git 和管理包样例。独立 grader 的最终行为检查不能被 Agent 通过修改项目测试削弱。

## B3 任务与证据记录

实现 task/evidence 模板和 state 模块，完成 create/update/check。初始化与更新输入均带 schema_version=1，任务身份来自实际 workspace，记录原有修改边界、范围、计划、授权索引、进度和证据。host_run 用固定 host_context 保存实际宿主、模型、场景与包/策略 hash，不通过无结构的备注冒充这些信息。

apply 前使用排他锁；锁内做 revision、原内容和数据一致性检查，然后同目录原子替换。并发相同 revision 只能一方写入，后者报冲突；默认不自动删除遗留锁。

证据登记证据 JSON、raw 文件的实际 hash 和验证对象指纹；代码、测试、raw 或证据自身变化后明确失效，不能只检查文件存在。不要从 approved=true、completed=true、文件来源标签或其他 Agent 意见生成用户授权。存在完成阻断项时不能把状态改成可交付完成。

覆盖身份串用、证据缺失、非法执行状态、用户编辑、CAS 冲突、文件变化和恢复。工具只管理与核验记录，不新增自动任务执行器。

## B4 两端适配

实现 adapters/zcode 和 adapters/codex 的清单、市场模板、界面元数据和能力说明。ZCode 使用原生清单及只读 Reviewer 定义；Codex 使用可移植清单和已实际支持的原生审查入口，不复制未知 Agent 字段。

两端共享技能正文、策略和 reviewer-contract，仅包装与工具映射不同。策略和工具在安装后可定位，不假设 cwd 或源码位置等于插件目录。

核对最新官方文档、实际运行时与 --help，不猜 API、配置字段或 flag。能力分 discovery、explicit_invocation、automatic_selection、policy_loading、native_subagents、reviewer_restriction、workspace_isolation，逐项标 verified/unverified/unsupported/failed；只读限制说明真实 enforcement。

本机曾观察到终端 codex wrapper 的原生二进制缺失。重新探测现有官方 CLI/桌面入口，不以 PATH 存在推导可用，也不修补全局程序绕过。

## B5 产物与文件管理

实现 build、package_check、owned_files 和完整 CLI。生成两端自包含目录、市场文件、ZIP 候选、artifact 和发行 index，核实同源内容 hash 的可复现性。

每个包包含完整的技能、策略、模板、工具、schema、来源及许可证；策略正文和共同技能两端一致。记录实际 source revision、dirty 状态和源内容 hash。不得夹带工作记录、恢复快照、auth、用户 home 路径或未登记文件。

files plan 不改目标，只输出显式指定的报告；apply 使用原 operation_id 重新预检查源与目标、核对计划 hash 和 receipt，并使用目标锁，不重新生成 ID/时间戳误判有效计划过期。完全无变化时不改 receipt、不产生备份。只管理规格限定的 staged 子目录，不把整个 target 当自有目录。

覆盖重复暂存、未拥有文件、用户编辑、过期计划、源漂移、路径逃逸、符号链接、额外活动组件、并发和中断。remove 只删自有且未被用户修改的文件。回退使用验证过的旧包形成正常 update，不加 force 绕过保护。

在新核心、工具、产物、引用和适用安全测试通过，历史记录和 BEL 许可证迁入完成后，删除已替代的仓库内 zcode-workflow 原入口。迁移映射和历史验证状态保留可追溯性；不卸载用户实际安装的旧插件或改其全局规则。

## B6 真实会话验收

完成 prepare/collect/grade，collect 严格使用验收矩阵固定的材料输入清单及 source_path/target_path 映射。手工归一化与原生转换分别标记，不猜测未知原生格式；每端都提供可导入真实材料的手工路径。先显式调用，再验证自动选择和完整任务；使用实际客户端与用户现有模型，保存原始运行、actor/工具顺序、初始/最终状态、RED/GREEN 和审查证据。

严格按验收矩阵执行声明支持组合。A01 至 A22 每宿主至少一次，关键集合每宿主至少三次；A23 至 A25 做真实管理与产物检查，宿主安装另有实际加载证据。原生对照按规定场景、同模型和相同用户要求执行，环境混杂时说明而不宣传效果。

collect 不补造事件；manual_annotation 不冒充 native_export。grade 不用执行者写 pass 替代证据，无法证明的项目保持 manual_review/not_run/blocked_env。不能拿其他模型、Codex 规则推演或静态文本检查冒充 ZCode/GLM 实测。

环境阻塞时记录具体入口、命令/错误和所缺条件，继续完成 B1 至 B5 及 B7。只有代码、包和文档完成时按规格写 implemented_with_acceptance_blocked，T07 仍未完成；不能写一次性全部验收通过或可发布。

## B7 发布准备和最终 Review

完成英中 README、usage、installation、migration、support-matrix、NOTICE、BEL 许可证保留和最小 CI。明确候选是解压后按原生方式注册，不假定客户端直接安装 ZIP。

CI 只做本地工具、包和 lint，使用受支持的维护基线，不调用模型、不嵌入凭证、不自动发布。支持与限制依据真实结果，不把目标平台写成已经普遍验证。

统一测试入口必须包括汇总器自身测试、保留契约、新增 Python 单元/集成、包检查。处理空集合、缺测试和异常退出，不能假绿。工具覆盖率目标至少 80%，报告实测范围；静态覆盖率不代替模型行为验证。

每批次先有效 RED 再 GREEN/重构；纯文档检查相应结构与引用。最终跑所有适用测试、lint、产物检查、引用检查和 git diff --check。新改动只在影响或发现问题时增加复验，不无理由反复跑全量。

对最终实际 diff 和新增文件做独立 Review；若确无独立能力，记录具体原因、自查范围和限制。主执行者核实发现、修复确定严重问题并复验后交付，不把实现者或子 Agent 的完成声明当作通过证据。

## 最终交付

交付时明确 implemented、accepted、release_candidate 或 implemented_with_acceptance_blocked 的实际层级，并逐项列出 T01 至 T08 的完成/未完成依据。

提供实现文件与效果、迁移映射、恢复快照、两端产物路径及 hash、所有测试/覆盖率/静态检查结果、真实运行结果与证据、审查问题处理、支持限制和待用户操作。所有未运行、失败或阻塞如实说明。

代码和文档保留未提交状态，最终交给用户 Review。持续推进全部已授权可执行工作，不能以进度总结、完成一个阶段或预算猜测代替本轮交付。
