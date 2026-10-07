# AI 工作流首版数据契约

迁移说明（2026-10-07）：本文件保留首版设计基线，源码路径现相对
`plugins/ai-code-workflow/`。仓库级目录注册、通用清单元数据、独立插件版本
和 schema_version=2 发行索引以
[多插件规格](../../../../docs/design/2026-10-07-multi-plugin-design.md) 为准；
原 workflow 行为与任务/证据契约仍由本插件维护。历史执行 Prompt 不构成
当前授权，历史验证结果不因迁移获得新的通过声明。

本文固定实现规格中使用的数据字段、校验规则、模块接口和路径语义。JSON 示例用于说明格式；时间、消息引用和哈希必须来自实际运行，执行者不能复制示例值冒充证据。本插件任务、证据、策略与 artifact 使用 schema_version=1，并拒绝重复 JSON key、未知字段和不合法类型；公共发行 index 的 schema_version=2 见多插件规格。

## 产品来源

本插件根 product.json 是产品身份、版本及资源白名单的唯一来源，即仓库的 plugins/ai-code-workflow/product.json。仓库 package.json 保持内部包名 ai-code、private=true，不再与插件版本绑定。两端发行清单的 name 使用 product_id，不用 Node 内部包名推导身份。

```json
{
  "schema_version": 1,
  "product_id": "ai-code-workflow",
  "display_name": "AI Code Workflow",
  "version": "2.0.0",
  "repository": "https://github.com/Zack-Zz/ai-code",
  "license": "MIT",
  "hosts": ["zcode", "codex"],
  "profiles": ["collaborative", "continuous"],
  "generated_agents": [
    {"host": "zcode", "template": "adapters/zcode/agents/workflow-reviewer.md", "body": "skills/review/references/reviewer-contract.md", "target": "agents/workflow-reviewer.md"}
  ],
  "core_skills": ["workflow", "tdd", "debugging", "review", "verification"],
  "shared_skills": ["review-results"],
  "resources": [
    {"source": "policies", "target": "policies", "include": ["collaborative.json", "continuous.json"]},
    {"source": "schemas", "target": "schemas", "include": ["product.schema.json", "policy.schema.json", "task.schema.json", "evidence.schema.json"]},
    {"source": "templates", "target": "templates", "include": ["task.json", "evidence.json"]},
    {"source": "skills/review/references", "target": "skills/review/references", "include": ["reviewer-contract.md"]},
    {"source": "scripts/workflow_tool.py", "target": "tools/workflow_tool.py", "include": []},
    {"source": "scripts/workflow", "target": "tools/workflow", "include": ["__init__.py", "product.py", "policy.py", "state.py", "build.py", "package_check.py", "owned_files.py", "cli.py", "io.py"]},
    {"source": "LICENSE", "target": "LICENSE", "include": []},
    {"source": "NOTICE", "target": "NOTICE", "include": []},
    {"source": "LICENSES", "target": "LICENSES", "include": ["backend-engineering-lite.txt"]}
  ]
}
```

2026-10-07 增加的 hosts/profiles/generated_agents 是公共工具消费的声明元数据。
通用清单要求 hosts 非空，技能/profile/Agent 列表可为空；本插件仍严格保留
两个既有宿主、两策略、六技能及上例唯一 Reviewer 合成，不因通用扩展而放松。
该合成只使用模板 frontmatter 加共享正文，不运行任意代码 hook。

product_id 使用小写 kebab-case，version 使用 X.Y.Z。core_skills 和 shared_skills 不重复，名称必须对应 skills/<name>/SKILL.md。资源 source 和 target 为规范化相对路径，拒绝绝对路径、父目录逃逸、符号链接和映射冲突。

source 为文件时 include=[]；为目录时 include 是明确的相对文件列表，不接受通配符、表达式或自动递归收集。按相对路径排序，不登记 __pycache__、.pyc 等缓存；未登记的新文件不能被自动带入包。SKILL.md 以首个 frontmatter 为元数据，源格式限定为单行 name、description 和可选 origin；不实现通用 YAML 解析器。

技能正文和默认策略在两端包中应同哈希。Codex 界面元数据在 adapters/codex/interfaces.json 维护六个技能的 display_name、short_description、brand_color、default_prompt 和 allow_implicit_invocation，生成各自 agents/openai.yaml。现有 review-results 的界面字段迁入该来源，旧源位置在映射核验后退出，避免两份元数据。

## 策略字段与解析顺序

完整 profile 的字段如下，全部必填。项目覆盖文件必须有 schema_version，其余字段可部分提供。

```json
{
  "schema_version": 1,
  "mode": "collaborative",
  "review_level": "critical",
  "max_parallel_tasks": 2,
  "response_language": "auto",
  "verification_notes": []
}
```

| 字段 | 约束及默认行为 |
|---|---|
| mode | collaborative 或 continuous；两份 profile 仅此字段不同 |
| review_level | critical 或 all；critical 要求 critical 风险任务尝试可用独立审查，all 进一步要求其他实施任务也尝试；无能力仍按契约报告限制 |
| max_parallel_tasks | 1 至 8 的整数，默认 2；实际并行还受宿主容量与适用用户要求限制 |
| response_language | auto，或格式合法的语言标签，如 zh-CN、en；auto 跟随用户语言 |
| verification_notes | 最多 16 条、每条最多 512 字符的项目验证要求；不能作为执行任意命令的授权 |

解析顺序为：collaborative 完整默认 → 项目文件 → 本次用户显式选项。用户显式选 continuous 时，读取对应完整 profile 作为默认，再应用项目文件，但最后的显式 mode 仍优先。其他显式字段同样逐字段优先。项目文件写 mode=continuous 只表达偏好，不能批准任务实施。

输出字段为 effective_policy、sources、warnings、policy_hash。sources 为每个有效字段的来源和路径或用户输入标识。policy_hash 对规范化后的有效策略 JSON 做 SHA256，不能包含不稳定构建时间。

策略错误返回退出码 2。禁止出现 approved、auto_commit、model、api_key 等未定义字段；已有用户明确授权的 Git 操作通过实际消息识别，不能靠策略开关自动授予。

JSON 中的 true/false 不能因为 Python 的 bool 是 int 子类而被当作 revision 或并行数；整数检查必须排除 bool。任务字段和操作计划中的同类整数遵循相同规则。

## 任务记录与初始化输入

任务目录为 workspace/.ai-workflow/tasks/<task_id>/，task_id 匹配 `^[a-z0-9][a-z0-9_-]{0,63}$`。workspace 必须是明确目标工作区的规范绝对路径，不能使用 ID 拼接越界。

task create 的 input 只接受 schema_version=1、plan、authorization_refs、protected_paths，全部必填；workspace、baseline、record_revision、时间由工具计算，调用者不能提供这几项。templates/task.json 是该初始化输入的模板；task.schema.json 同时描述初始化、更新和持久化记录三个固定结构。

| 持久字段 | 类型与约束 |
|---|---|
| schema_version、record_revision | 整数；新任务 revision=1，每次实际更新加 1 |
| task_id | 与目录身份一致 |
| workspace | root、repository_root、git_head；root 必填，非 Git 项目的后两项可以为 null |
| baseline | dirty_files 和 protected_fingerprints；记录创建时实际观察到的原有修改，指纹只计算相关保护路径 |
| plan | revision、goal、scope、acceptance、change_type、risk、depth；全部必填 |
| progress | phase、status、completed_steps、next_action、unresolved；全部必填 |
| authorization_refs | 用户消息来源、明确动作及适用范围的引用列表 |
| evidence_refs | 任务目录内证据 JSON 的 relative_path 与 content_sha256 列表 |
| created_at、updated_at | 工具生成的 UTC RFC3339 时间；对用户展示按客户端时区转换 |

plan.scope 为工作区内相对路径或目录前缀数组，至少一项；不接受 ../、绝对路径或 shell 表达式。它是范围描述，不是可直接执行的删除列表。plan.acceptance 是明确的可观察完成条件数组，不能仅写完成任务。

change_type 为 feature、bugfix、refactor、documentation、configuration 之一。risk 为 normal、critical；depth 为 short、standard、architectural。纯只读任务默认不创建文件记录，用户明确要求保存调查结果时才允许创建规划记录。

progress.phase 为 planning、implementing、verifying、reviewing、handoff；status 为 awaiting_confirmation、in_progress、blocked、ready_for_user_review。completed_steps 记录实际完成的步骤标识；unresolved 每项为 kind、summary、severity、completion_blocking、evidence_ref，kind 分 confirmed_defect、risk、environment、question；severity 为 critical、high、medium、low 或 null。

confirmed_defect 且 severity 为 critical/high 时 completion_blocking 必须为 true。仍存在 completion_blocking 项时，不能将任务设为 ready_for_user_review。未知风险不因等级标签自动变成确定缺陷；是否阻塞取决于适用任务要求和实际证据，必须解释依据。

authorization_refs 每项为 message_ref、actions、scope_summary。actions 只允许 plan、implement、run_tests、diagnose_write、commit、amend、tag、push、merge、create_pr、install、publish。这些字段是审计索引，CLI 不负责判定消息真伪，不从记录调用 Git、安装宿主或发布。Agent 仍须核对实际用户消息。

task update 的 input 必须有 schema_version=1，另只接受可选 plan、progress、append_authorization_refs、append_evidence_refs，至少一项。不能改 task_id、workspace、baseline、created_at 或任意写 revision。plan 实质变更时 plan.revision 加 1，执行者确认适用授权是否覆盖新范围；CLI 不能凭新增 ref 断言用户已经确认。

task create/update 默认只返回 proposed_record、changed、applied=false。--apply 才实际写入；内容完全相同不增加 revision。成功输出 applied=true、record_revision 和记录路径。

写锁路径为任务目录的 .write.lock，使用 O_CREAT|O_EXCL 创建，内容包含 operation_id、PID 和创建时间。所有读取比较、更新与原子替换在锁内完成。正常结束只删除本操作 token 对应的锁；锁存在返回退出码 3，不能自动按过期时间删除。

## 证据结构和失效判断

模板 evidence.json 是填写事实的输入，不是通过证明。每条证据存为任务目录 evidence/<evidence_id>.json，raw 记录存为该任务目录内的独立文件；evidence_id 使用同 task_id 的名称规则。

| 字段 | 约束 |
|---|---|
| schema_version、evidence_id、kind | kind 为 test、review、inspection、host_run |
| workspace_root | 与任务身份匹配的绝对路径 |
| subject_fingerprints | 相对文件路径到 SHA256 或 null 的映射；null 表示该状态下文件不存在，不能表示未知 |
| execution | null，或 argv、cwd、exit_code、signal、start_error；不将 argv 拼成 shell 字符串执行 |
| host_context | host_run 必须为 host、host_version、model、case_id、package_content_hash、policy_hash 的对象；其他 kind 为 null |
| capture | origin、relative_path 和 content_sha256；origin 为 tool_output、native_export、manual_annotation，路径留在任务目录内，hash 来自实际文件 |
| result | pass、fail、not_run、blocked_env、needs_revalidation、manual_review |
| observations | 已观察事实的简短字符串数组，不放无必要的完整会话或凭证 |
| started_at、finished_at | 已实际运行的证据为工具观察时间；未运行允许 null |

test 的 pass 要求 execution 非空、exit_code=0、signal 和 start_error 均为 null，并有实际结束时间和捕获记录。host_run 的 host_context 必须与实际材料索引一致，host 为 zcode 或 codex，case_id 为 A01 至 A25；没有取得的版本或模型信息填 null，并保持 manual_review/not_run/blocked_env，不能判 pass。还须有相应场景结果，只有进程启动不能判 pass。review/inspection 允许 execution=null，但须说明真实读取或审查来源；无法确认语义时用 manual_review。

host_run 提供 execution 时，pass 同样要求 exit_code=0、signal/start_error=null；不得将明确失败的运行登记成 pass。execution=null 仍可用于具有原生导出材料的宿主会话，是否真正通过场景由独立验收判断。哈希字段必须为字符串并完整匹配 64 位小写十六进制，布尔值、数字、对象或尾随换行均拒绝。

登记 evidence_ref 时计算证据 JSON 的内容哈希，并验证 capture 路径和其实际 content_sha256。证据后来被编辑、raw 文件缺失或内容变化、subject 文件改变、工作区身份不一致或执行状态不成立，task check 返回具体失效原因。不能只判断 raw 文件存在。证据没有被登记的文件范围不能自动视作已覆盖。

task check 输出 identity_status、invalid_evidence、pending_items 和 consistent。consistent=true 只表示记录和当前文件一致，不表示业务结果已正确，也不会自动将任务设为 ready_for_user_review。

## 自有文件计划和 receipt

files 的 target 为项目或隔离测试根。管理根是 target/.ai-workflow/staged/ai-code-workflow，receipt 是 target/.ai-workflow/receipts/ai-code-workflow.json。目录本身不是整个 target 的所有权凭证。

receipt 字段为 schema_version、product_id、version、managed_root、artifact_hash、files、last_operation_id；files 映射相对路径到实际 SHA256。未经 receipt 记录的文件不属于本工具，即使文件内容和目标完全相同。

plan 字段为 schema_version、operation_id、action、source_package、source_artifact_hash、target_root、managed_root、receipt_before_hash、items、conflicts、plan_hash。items 每项为 relative_path、operation、expected_before_sha256、desired_sha256，operation 为 create、replace、delete、keep。null 表示预期不存在或删除后的不存在。

plan_hash 对不含自身的规范化 JSON 计算 SHA256。operation_id 在 plan 阶段只生成一次，apply 重算时使用该合法原 ID，不重新生成随机 ID 或加入当前时间。重算比较源、目标、receipt、items 及冲突；不能因正常重算中的新 nonce 误判计划过期。

apply 不只信任 items：stage/update 重新验证 source package，读取 receipt，并重新产生同一预期计划；存在冲突、源漂移、目标漂移或 hash 不符均拒绝写入。stage/update 的额外未拥有文件形成冲突；remove 的额外未拥有文件保留并报告。remove 的 source_package 与 source_artifact_hash 为 null，其输入依据是实际目标 receipt。

若所有 items 都是 keep，且版本、artifact 和 receipt 已一致，apply 返回 changed=false、applied=false，不改 receipt 的 last_operation_id、不产生备份或 pending 日志。已存在同 operation_id 的恢复资料且操作未明确完成时返回冲突，不覆盖旧恢复资料。

上述无变化规则仅适用于 update；remove 即使所有托管文件已缺失，仍须备份并删除归属正确的 receipt，完成所有权生命周期。版本或 artifact_hash 不一致属于真实元数据更新。所有操作都核对 receipt.managed_root；apply 对 receipt 的存在与不存在也做冲突比较，已有回执在更新期间消失不得重建。写入包文件使用一次受控读取的字节计算哈希并发布这些字节，receipt.version 来自已校验的包快照。

apply 取得该产品目标的排他锁后，再读取和比较 receipt 及所有相关原内容。锁位于 receipts 目录中，不进入发行包。操作前保存旧自有文件与 receipt 到 backups/<operation_id>/，并保存 pending-operation.json。

每次文件替换后更新操作记录；全部完成再写入最终 receipt 并移除 pending 标记。中断可能发生在文件与日志之间，恢复判断必须同时比较实际文件的旧/新预期哈希，不仅相信日志。遇到其他内容保持冲突，不能盲目重放。

下一次发现 pending 或遗留锁时返回退出码 3 和恢复依据，默认不自动恢复。remove 只删除 receipt 中哈希仍相符的自有文件，保留其他内容；不能删除整个工作区、用户配置目录或原生宿主缓存。

## 发行包记录

artifact.json 字段为 schema_version、product_id、version、host、profiles、source_revision、working_tree_dirty、source_tree_hash、files、content_hash。

host 为 zcode 或 codex；profiles 固定含 collaborative、continuous。source_revision 记录实际 Git HEAD 或 null，dirty 如实反映构建输入来源。source_tree_hash 覆盖身份、来源组件、资源和对应 adapter 输入；仅写 HEAD 不能证明未提交源码的具体内容。

构建使用私有来源快照的实际字节计算 source_tree_hash；包复制、生成的 adapter 内容与该捕获输入一致，复制期间变化或 mutate-copy-restore 不得使包内容脱离其来源哈希。Git 上下文在创建工具自己的暂存目录之前捕获，避免把构建临时文件算作用户的 dirty 来源。包扫描按 lstat 枚举非目录成员，未登记的 FIFO 等特殊文件必须拒绝，不能因 is_file=false 而漏过闭包检查。

files 为相对路径与 SHA256 的排序列表，不含 artifact.json 自身，避免自引用。content_hash 对 files 的规范 JSON 计算 SHA256，并由检查器重算；检查器还核对首版必需组件。时间戳和临时绝对路径写入构建报告，不进入可复现哈希。

CI 对每份 ZIP 验证其自身校验和及与目录的逐文件一致性，再比较两份产物的内容和稳定元数据。仅 source_revision/working_tree_dirty 可因提交环境不同而变化；不能跨 Git 上下文要求 ZIP 字节相同。同一源码、适配输入和 Git 上下文的重复构建仍须字节一致。

package check 检查 files 完整性、额外活动组件、清单和市场解析、技能资源引用及版本一致性。目录存在或 product_id 正确不能替代这些检查。

## 宿主能力和结果状态

每个宿主组合记录 host、host_version、model、package_content_hash、policy_hash、tested_at 和 capabilities。capabilities 的键为 discovery、explicit_invocation、automatic_selection、policy_loading、native_subagents、reviewer_restriction、workspace_isolation。

每项为 status、evidence_refs、notes；status 为 verified、unverified、unsupported、failed。reviewer_restriction 另有 enforcement，值为 host_allowlist、policy_only、none、unknown。不从配置文件存在推导 verified，不把别的宿主或模型的测试移用。

交付层状态只有 implemented、accepted、release_candidate、implemented_with_acceptance_blocked。implemented 要求工具测试及产物完成；accepted 要求声明范围的实际行为验收完成；release_candidate 还要求来源、文档及独立审查闭环。任何状态都不等于已获得发布授权。

## 主要模块函数接口

这些是模块职责接口，实现者可增加内部小函数，但不能改变核心输入输出语义或新增自动外部行为。

| 模块接口 | 返回与关键行为 |
|---|---|
| product.load_product(root) | 合法 ProductSpec；检查身份、组件、资源与版本，不写文件 |
| policy.resolve_policy(plugin_root, workspace, explicit_options) | 有效策略及来源/hash；explicit_options 必须来自实际用户选择 |
| state.create_task(workspace, task_id, input_data, apply=False) | 预检查或新记录，系统字段由实际环境生成 |
| state.update_task(workspace, task_id, expected_revision, input_data, apply=False) | 锁内校验并更新；重复无变化不增加 revision |
| state.check_task(workspace, task_id) | 身份、证据及待核实项；只读，无自动执行 |
| build.build_packages(source_root, hosts, output_root) | BuildReport、实际包目录和记录；不安装、不发布 |
| package_check.check_package(package_root, host) | 验证结果及问题；失败非零，不根据文本关键词断言运行时成功 |
| owned_files.plan_operation(package_root, target_root, action, operation_id=None) | 无目标副作用的 FilePlan；初次生成 ID，apply 重算传入原 ID |
| owned_files.apply_operation(plan, expected_plan_hash) | 重新预检查、锁和逐文件操作结果；冲突不覆盖 |
| io.load_json(path) | 拒绝重复 key、超出大小和格式错误 |
| io.resolve_member(root, relative_path) | 返回受控路径；拒绝越界、符号链接及不合法类型 |
| io.atomic_write(path, bytes, expected_before) | 在调用者排他锁内比较原内容并原子替换 |

所有返回对象经 CLI 转成清晰 JSON。可变容器采用新对象构造，测试不依赖隐藏全局状态。

## 必须覆盖的数据与边界测试

1. 产品重复组件、缺失来源、错误版本、路径逃逸及资源映射冲突。
2. 两种 profile、项目部分覆盖、用户显式覆盖、无效/未知/重复字段、模式不生成授权。
3. 新任务实际 baseline、重复 ID、错误 workspace、计划 revision、更新不改变系统字段。
4. 两个并发更新者使用相同 revision，只有一个实际写入；后一个不能覆盖先一个。
5. 证据缺失、证据 JSON 或 raw 内容修改、源码/测试修改、错误退出状态和未运行结果不能冒充 pass。
6. 同源重复构建的内容哈希一致，dirty 源码不会被伪装成干净 release。
7. 未拥有内容、用户编辑、过期计划、源变化、符号链接以及中断更新不发生盲目覆盖；有效计划重算不会因 ID 改变失败，完全无变化时不创建新备份。
8. remove 只处理自有文件，备份与 raw 记录不进入包，额外活动组件被包检查发现。

这些测试验证工具行为；授权语义、自动选择、真正只读能力和最终业务结果仍按真实会话矩阵检查。
