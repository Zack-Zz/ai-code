# AI 工作流首版实现规格

迁移说明（2026-10-07）：本文件保留首版设计基线，源码路径现相对
`plugins/ai-code-workflow/`。仓库级目录注册、通用清单元数据、独立插件版本
和 schema_version=2 发行索引以
[多插件规格](../../../../docs/design/2026-10-07-multi-plugin-design.md) 为准；
原 workflow 行为与任务/证据契约仍由本插件维护。历史执行 Prompt 不构成
当前授权，历史验证结果不因迁移获得新的通过声明。

本规格将任务设计落实到明确的模块、文件、命令、算法和交付标准，供实现 AI 直接参考。它仍是待用户确认的设计，不代表已实施。业务行为见[验收矩阵](2026-10-01-workflow-v1-acceptance.md)，字段细节见[数据契约](2026-10-01-workflow-v1-data-contracts.md)；本规格中的命令是未来工具接口，目前不能据此宣称命令已经存在。

## 已确定的技术选择

| 项目 | 首版选择 |
|---|---|
| 仓库 | 沿用 ai-code，不创建新仓库，不恢复已退役产品 |
| 插件标识 | `ai-code-workflow`；区别于旧 BEL，避免把新包覆盖到旧插件身份下 |
| 展示名 | `AI Code Workflow` |
| 候选版本 | `2.0.0`，沿用当前元数据作为未发布候选，不打 tag、不宣称已发布 |
| 身份与组件来源 | 本插件根 `product.json`；两端清单注入该插件身份/版本，仓库 package.json 不再绑定插件版本 |
| 核心 | workflow、tdd、debugging、review、verification 五类能力；另保留 review-results 作为共用呈现技能 |
| 管理工具 | Python 3.11+ 标准库；Node 22+ 用于源码维护和统一测试；开发和 CI 基线为 Python 3.13、Node 22 |
| 工具依赖 | 不编写通用配置语言或 JSON Schema 引擎；对本产品固定结构做类型、字段、枚举及边界校验 |
| 模型 | 使用用户现有选择，不自动指定、切换或降级模型 |
| 首发宿主 | ZCode、Codex；对外支持声明只覆盖实际验收过的版本、模型和环境 |
| 公共渠道 | 准备 Git 仓库及本地市场发行候选；npm 继续 private，不执行任何外部发布 |
| 运行记录 | 工作区 `.ai-workflow/`，不进入源码或发行包 |

首版只实现两种协作模式：collaborative 和 continuous。默认 collaborative；continuous 仅改变已明确授权范围内的计划确认节奏，不增加任何 Git、安装、外部写入或模型权限。

运行版本选择依据[Node 官方版本状态](https://nodejs.org/en/about/previous-releases)和[Python 官方版本状态](https://devguide.python.org/versions/)。旧 BEL 的历史要求仍按迁移记录保存；新维护基线不继续承诺已退出支持的 Node 18、Python 3.9。原生 Markdown 技能不要求用户安装 Node，Python 管理工具只在使用对应功能时需要。

## 目录和文件职责

以下源码路径现相对 `plugins/ai-code-workflow/`。首版 scripts、schemas 等目录服务本插件，不恢复清理前的旧实现；仓库 tests 汇总器、CI 与公共 dist 仍在仓库根。

| 路径 | 职责 |
|---|---|
| `product.json` | 产品身份、版本、组件和资源白名单 |
| `skills/workflow/SKILL.md` | 任务分类、有效策略、范围、计划和执行组织；按阶段加载必要技能 |
| `skills/tdd/SKILL.md` | 有效 RED、GREEN、重构基线和环境阻塞处理 |
| `skills/debugging/SKILL.md` | 事实与假设、复现、最小实验、停止无证据试错 |
| `skills/review/SKILL.md` | 风险审查、独立 Reviewer、主 Agent 核实、按影响范围复审 |
| `skills/verification/SKILL.md` | 最终状态、验证层级、证据失效、完成与交付声明 |
| `skills/review-results/` | 单一审查呈现契约，其他技能引用，不复制第二份正文 |
| `policies/collaborative.json`、`policies/continuous.json` | 两种受控默认策略 |
| `schemas/product.schema.json`、`policy.schema.json`、`task.schema.json`、`evidence.schema.json` | 描述固定的数据契约，供文档、测试和其他消费者使用 |
| `templates/task.json`、`templates/evidence.json` | 新任务和证据输入模板，示例标识不能当作真实授权 |
| `adapters/zcode/` | ZCode 清单、市场模板、Reviewer 工具映射和能力说明 |
| `adapters/codex/` | Codex 可移植清单、市场模板、界面元数据和原生审查能力说明 |
| `skills/review/references/reviewer-contract.md` | 共享的只读审查职责正文，两端共用；工具配置由 adapter 实现 |
| `scripts/workflow_tool.py` | 单一管理工具入口，仅分派本规格的文件与校验操作 |
| `scripts/workflow/product.py`、`policy.py`、`state.py` | 固定数据校验、策略解析、任务与证据管理 |
| `scripts/workflow/build.py`、`package_check.py`、`owned_files.py` | 包生成、产物验证、自有文件预检查和更新 |
| `scripts/workflow/cli.py`、`io.py`、`__init__.py` | 参数处理、统一 JSON 读写与路径保护 |
| `tests/workflow/` | Python 单元及临时目录集成测试，按模块组织 |
| 仓库根 `tests/run-suite.js`、`tests/run-suite.test.js` | 公共工具与各插件真实退出状态汇总、自身测试 |
| `tests/skills/` | 核心技能契约及实际引用检查，不把关键词检查当作模型行为验收 |
| `evals/cases.json`、`fixtures/` | A01 至 A25 的数据化定义、一次性 Python/JS 样例 |
| `evals/prepare.py`、`collect.py`、`grade.py` | 样例准备、原生或人工记录导入、分项检查；不建设 Agent 调度服务 |
| `docs/usage.md`、`installation.md`、`migration.md`、`support-matrix.md` | 使用、安装、迁移和实际支持范围 |
| `.github/workflows/ci.yml` | 新的最小源码 CI：本地工具测试、包检查和 lint，不调用模型、不执行发布 |
| `README.md`、`README.zh-CN.md`、`NOTICE`、`LICENSES/backend-engineering-lite.txt` | 英文入门、中文入门、来源和 BEL 许可证保留；根 LICENSE 原声明保留 |
| `dist/` | 可删除并可复现生成的受控产物，不能包含工作记录或临时样例 |

每个模块以一个明确职责为边界。保持小函数和聚焦文件；因实际复杂度拆文件时，在文件级计划中说明，不新增无使用场景的抽象层。

## 核心技能的执行契约

### workflow

进入后先识别只读任务或开发任务，再确认 workspace 身份和原有修改。只读任务直接形成答案或审查结果，不写任务文件或测试，不强行走实施流水线。

开发任务依次形成目标、范围、验收条件、变更类型、风险和适用授权。计划深度为 short、standard、architectural；风险为 normal、critical。这两个维度相互独立，单文件鉴权可以是 short 计划和 critical 风险，文件多不自动等于 critical。

collaborative 模式先给与范围相称的计划，收到适用的用户确认后进入实施；已有总体计划确认不重复询问。continuous 模式仍先说明简短计划，但用户已明确授权执行的范围可继续推进。仅将模式设置为 continuous 不构成授权。

进入实施时加载 tdd；根因不明时使用 debugging；交付前使用 verification；实际变更触及审查维度时使用 review。重用既有信息，不每个工具调用都重读所有技能。

### tdd

功能、Bug 修复、可执行脚本及其他行为变化先写最小可观察行为测试并运行，确认失败原因来自目标行为。测试首次即通过、语法错误或环境失败都不能算有效 RED。

GREEN 只实现当前测试所需行为，再跑受影响测试。REFACTOR 保持绿灯，新增行为进入下一轮 RED。纯重构使用必要的现有行为测试和通过基线；文档及不改变执行行为的配置采用相应校验。

缺少有效测试环境时先处理已授权可安全解决的环境问题；仍不可运行则保留调查、报告阻塞，不默认先实现。发现自己先实现时保护已有修改，仅在能精确分离时回到本次 RED，不执行全仓 reset 或 checkout。

### debugging

先确定现象、预期、范围、最近变化和复现条件。每次最小实验写出能区分的假设、预期观察及实际结果。连续两次尝试没有增加证据时，返回假设与观测点，不继续猜测式修改。

定位后产生 tdd 的修复输入。临时诊断写入也受适用授权约束；手工恢复、HTTP 200 或偶然通过不作为根因已解决证据。

### review

输入为目标、约束、最终 diff、验证与修改归属。只检查受影响的正确性、鉴权、公共契约、并发和一致性等维度，不加载通用框架教程库。

critical 风险或 review_level=all 时尝试可用独立 Reviewer。给它明确范围、需求、diff 和证据，继承当前模型，优先使用宿主能够实际执行的只读限制。能力只有指令约束时标为 policy_only，不能宣称宿主已禁止写入；不可用或失败时明确自查范围和限制。

主 Agent 核实发现，修复后复验受影响范围。确定缺陷、待核实风险及建议分别列出，最终输出加载共用 review-results；已确认严重缺陷保持未完成状态。

### verification

将所有完成声明绑定到最终代码状态。验证层级区分源码审查、静态/编译、测试、服务可达、状态/持久化和业务结果。只报告实际达到的层级，不要求所有任务机械达到最高层级。

交付包括行为效果、本次 diff、实际验证、审查与问题处理、失败或未运行事项、剩余操作。验证后修改相关源码或测试，需要重新检查对应证据。交付待用户 Review 不触发 commit 或发布。

## 策略解析和生效

插件携带两份策略文件。workflow 在进入开发任务时从已加载技能的位置定位插件根，读取 collaborative 默认策略，再按用户显式选择的模式读取对应策略。不得假定当前目录等于插件安装目录，也不得硬编码用户 home。

工作区可选 `.ai-workflow/policy.json` 只覆盖允许的字段。当前任务中用户明确给出的同类选项优先于该项目文件。宿主系统/开发者限制及适用的用户操作授权始终独立检查，配置不能放宽它们。

策略文件格式无效、出现未知字段、重复 JSON key 或不合法值时报告具体错误，不静默回退成更宽松模式。没有项目文件是正常情况；文件存在却无效需要处理。

策略解析工具输出有效策略、逐字段来源、警告和内容哈希。技能可使用读取工具解析小文件，或调用随包提供的 Python 工具；不能只写一个 policies 目录而没有实际加载路径。

两端的包必须都包含策略、工具及模板，所有技能内资源引用在安装根内可解析。宿主原生 userConfig 值未证明能传入技能时，不以它作为策略生效机制。

## 管理工具接口

本插件目录内入口为 `python3 scripts/workflow_tool.py`；从仓库根调用 `python3 plugins/ai-code-workflow/scripts/workflow_tool.py`。公共发行入口为仓库根 `python3 tooling/plugin_tool.py`。工具只执行受控文件操作、构建和校验，不运行用户项目的业务命令，不执行 Git 变更，不调用模型、不创建后台 Agent 服务。

| 子命令 | 输入 | 输出与行为 |
|---|---|---|
| `validate --root ROOT` | 产品源码根 | 校验 product、组件、策略、模板和引用；结构无误退出 0 |
| `policy resolve --plugin-root ROOT --workspace ROOT [--mode MODE]` | 包位置、工作区、用户显式模式；还支持 review-level、max-parallel-tasks、response-language 和可重复 verification-note 的显式选项 | JSON 有效策略及来源；只读，不产生任何操作授权 |
| `build --host HOST --output DIR` | 已验证源码和受控输出目录；HOST 取 zcode、codex、all | 两端的自包含包、市场文件、artifact.json 和构建报告 |
| `package check --path DIR --host HOST` | 实际生成包 | 校验资源闭包、身份/版本、路径、内容哈希与市场解析 |
| `task create --workspace ROOT --id ID --input FILE [--apply]` | 合法任务初始化 JSON | 默认预检查；apply 后创建任务记录，已有任务不覆盖 |
| `task update --workspace ROOT --id ID --expected-revision N --input FILE [--apply]` | 合法更新和预期 revision | 默认预检查；成功写入 revision 增加 1，冲突不覆盖 |
| `task check --workspace ROOT --id ID` | 现存任务及工作区 | 返回身份与证据一致性、需复验项；不表示业务结果已经正确 |
| `files plan [--package DIR] --target DIR --action ACTION --out FILE` | 包、明确目标及动作；ACTION 取 stage、update、remove | 不修改目标的预检查；仅按显式 --out 写计划报告和哈希 |
| `files apply --plan FILE --expected-plan-hash HASH` | 受控计划及其哈希 | 重新检查实际目标及内容，再应用自有文件；输出已应用与未应用项 |

ROOT、DIR、ID、N 是参数占位符，不是固定路径。所有 path 以解析后的根和相对路径共同限定，拒绝越界、符号链接绕过、非普通文件及未拥有的冲突内容。文件计划不能包含任意命令。

源仓库的 validate/build 服务维护者；随包工具的 policy/task/package/files 使用明确的包和 workspace 参数，不依赖原源码仓库路径。files 的 remove 不需要 source package，使用目标 receipt；因此 --package 只在 stage/update 必需。版本回退通过验证过的旧包形成 update 计划，不提供绕过用户编辑保护的 force 模式。

工具出口统一为：0 成功；1 验证或运行失败；2 参数/数据格式错误；3 内容或 revision 冲突；4 工作区身份不匹配或证据失效；5 要求的宿主环境不可用。错误须带稳定原因和相关路径，不把令牌或完整敏感数据放入输出。

## 数据和文件操作算法

JSON 输入按固定结构校验，拒绝未知字段、重复 key、类型不符及过大文件；结构上限 1 MiB，较大日志放独立证据文件。schema 文件记录外部契约，专用校验函数与有效/无效 fixture 对照验证，不建设通用 schema 解释器。

任务初始化检查 ID、工作区和目标路径，拒绝重复身份。任务写入先以 O_CREAT|O_EXCL 取得该任务排他锁，锁内读取当前 revision 和文件内容，比较调用者的 expected revision，校验更新后状态；写前再次检查原始内容。使用同目录临时文件、flush/fsync 和原子替换，成功后只释放本操作拥有的锁。不能仅做读比较再 rename，后者不能保证并发互斥。

写入进程中断后遗留的锁不按时间自动删除。返回冲突及具体锁路径，核实没有仍在写入的任务后由用户处理；默认工具不能代做不确定的锁恢复。files apply 同样使用产品目标的排他锁，避免 receipt 和文件集合被并发操作相互覆盖。

create/update/check 共用完整任务结构约束；check 同时校验 task_id、workspace、revision、嵌套结构，畸形 evidence_ref 逐项报告。任务和证据 JSON 经 workspace 根下的 no-follow 目录句柄读取，打开后 fstat 确认普通文件，以 1 MiB+1 的有界读取拒绝 FIFO 和增长中的超限输入。update 将同一读取快照解析并用于 expected_before，不能先读取旧字节再单独解析新文件。受保护文件与 subject 指纹只读取工作区内普通文件；缺失中间目录表示文件不存在，链接、越界或特殊文件报告无效。

排他锁保证本工具的写入者互斥，不是操作系统沙箱，也不能控制不遵守锁的外部编辑器。应用前再次核对相关文件，发现变化立即拒绝；使用目录句柄和 no-follow 等平台支持机制保护写入路径。无法安全应用的目标或平台应拒绝写入并说明限制，不用弱化检查作为兼容手段。

新文件使用排他发布拒绝后来的同名文件；替换前重验内容。POSIX 不提供对不遵守锁的外部写入者的内容 CAS，最终比较与 rename 之间仍有竞态窗口。不得宣称能完全隔离外部编辑；目录或内容变化已可观察时必须报冲突。

任务恢复只计算与当前范围相关的文件哈希，并与记录中的 workspace 和 subject_fingerprints 对比。不能从代码名称推断测试依赖；未记录的受影响范围由 Agent 定向补查。身份错误或证据漂移明确报告，不自动恢复 Git 或修改用户文件。

files plan 只接收 package check 已验证的组件集合。target 表示明确的项目或隔离测试根，实际管理根固定为 target/.ai-workflow/staged/ai-code-workflow，receipt 位于 target/.ai-workflow/receipts/ai-code-workflow.json，备份位于 target/.ai-workflow/backups/<operation_id>/。不将整个 target 当成自有目录。

逐项检查 receipt 的产品身份、目标根、历史文件哈希、当前文件类型与内容。未拥有文件即使内容相同也不能自动取得所有权；被用户编辑的托管文件拒绝覆盖或删除。stage/update 时管理根中的额外未拥有文件形成冲突，避免把未登记活动组件带入包；remove 保留这类额外文件并报告，不将它们列为删除项。

files apply 校验计划哈希，并重新计算预期源及目标状态，避免应用过期预检查。先保存本次将改写的自有内容和 receipt，再逐项替换，每步检查路径与原内容。中断后记录已应用项、未应用项和恢复依据；备份是恢复资料，不把整份旧配置盲目盖回去。

重算使用原 operation_id，不能重新生成 nonce 或时间戳使有效计划失效。所有文件、身份和 receipt 已一致时返回无变化，不创建新备份或只为记录新操作而改 receipt。证据检查同时核对 raw 内容 hash，不只核对其存在性。

自有文件工具只负责项目或隔离测试目录中的包暂存与管理。暂存成功不能称宿主安装或加载成功。宿主缓存、内部市场注册和常用用户配置不得由它直接改写，实际安装使用原生受支持方式。

## 构建与两端发行结构

产品、组件和资源白名单来自 product.json。构建先校验全部源码，在新的受控 staging 目录生成，再检查包闭包；目标中的非自有文件不清理。文件清单排序，JSON 编码和结尾固定，同源输入应产生同内容哈希。构建时间留在报告中，不作为可复现内容哈希的变化因素。

公共发行目录相对仓库根，分别为 `dist/zcode/ai-code-workflow/` 与 `dist/codex/ai-code-workflow/`；其聚合市场与新版 index 以多插件规格为准，以下保留本插件的包内容约束。每个包包含六份技能来源、policies、schemas、templates、tools、许可证与 NOTICE。两端可使用不同包装元数据，但共同技能正文和策略哈希应一致。

同时生成 zcode/codex 两个发行根的 ZIP 候选，包含对应市场文件及包目录，供下载解压后注册本地市场；不假定宿主能直接安装 ZIP。ZIP 条目排序、时间和权限固定，解压到新临时目录后重新进行包与市场检查。发行根的 index.json 记录目录、ZIP、市场文件及校验和；不把构建时间加入可复现内容。

ZCode 包使用 `.zcode-plugin/plugin.json`，生成原生 `agents/workflow-reviewer.md`，model=inherit，工具白名单仅 Read/Grep/Glob，maxTurns=12。市场文件在对应发行根，其 source 指向包目录。对实际客户端的支持以新会话验证为准。

Codex 包使用根 `plugin.json` 的可移植格式；必要的 OpenAI 界面信息放在 `extensions.com.openai`。仅在目标版本实测需要时才生成 `.codex-plugin/plugin.json` 兼容入口，不能让 overlay 与 inline settings 形成两套不一致来源。生成 `.agents/plugins/marketplace.json` 时按官方市场根语义解析 source.path。

Codex 不直接复制 ZCode Agent frontmatter。review 使用宿主实际支持的原生子 Agent 调用和能力映射；不能把未知 agents 清单字段写进去冒充支持。两端都在能力说明中标明 host_allowlist、policy_only、unsupported 或 unverified 的实际审查限制。

两端适配器都使用 skills/review/references/reviewer-contract.md 的正文；Codex 在原生调用中使用它，ZCode 生成 Agent 定义。实际加载后的包路径与 content_hash 必须与本次产物匹配，不能用旧缓存或设置页可见代替新包生效证据。

artifact.json 必须含产品、宿主、profile 集合、source revision、工作树 dirty 状态、源码内容哈希及每个文件的哈希。当前未提交源码生成的包必须如实标为 dirty。包不包含 eval 运行、工作区状态、恢复快照、auth 文件、node_modules 或用户 home 信息。

随包 CLI 在导入自身模块前禁用 Python 字节码写入，避免正常调用污染包目录。检查器将已识别的被动缓存与额外活动代码/配置分开报告，缓存不进入 hash 或 ZIP；未登记的 SKILL、Agent、MCP/Hook 配置或代码不能被当作缓存忽略。

格式依据为[OpenAI 插件包装](https://developers.openai.com/plugins/build/plugins)与[ZCode 插件](https://zcode.z.ai/cn/docs/plugin)。文档格式支持不等于本机运行时可用，执行者须记录实际版本和探测结果。

## 真实验收工具与运行方式

prepare 按 cases.json 中允许的 fixture 名复制一次性样例，写入基线和场景输入。fixture 路径必须留在 evals/fixtures 内，输出目录不得覆盖用户业务仓库。

collect 导入实际原生运行导出或有来源的人工记录，保存工具顺序、消息角色、diff、测试结果和环境信息。原始私有记录放 `.ai-workflow/eval-runs/<run_id>/`；对外报告只保留脱敏证据。人工标注不能标成原生自动捕获。

grade 对确定性结果做直接检查：文件哈希、测试退出状态、最终业务结果和可取得的调用顺序。对无法程序证明的用户授权或审查语义，使用明确人工或模型评审并记录方式；不能由执行 Agent 自己写 pass 代替证据。

Codex 优先使用实际可用的官方 CLI 或桌面原生会话；ZCode 使用经过实测的官方入口。当前终端的 codex wrapper 存在，但 2026-10-01 探测 --version/插件帮助均因原生二进制缺失而 ENOENT；这不证明桌面端不可用，也不能算加载测试成功。执行时重新探测，不擅自修补应用目录或全局运行时。

模型和登录使用用户现有且明确允许的环境。无隔离测试方式、无法登录、不能取得所需导出、运行时不可用等情况标为 blocked_env。可以完成其他实现和发行准备，但 T07 对应组合保持未完成，不能用另一个模型、静态模拟或同一助手的口头推演替代。

不自动重启正在运行的桌面应用、关闭其他聊天或停用用户现有插件。需要客户端刷新或新会话时选择宿主支持的安全入口；必须由用户完成的登录、重启或隔离操作作为具体待办记录，不能无限重试，也不能因此停止不受影响的本地实现。

## 实施批次与文件级任务

| 批次 | 对应任务 | 文件和完成条件 |
|---|---|---|
| B0 | 前置核验与最小收尾 | 保存当前工作区差异和未跟踪资产的可恢复副本；将汇总器自身测试注册到默认 npm test，按 TDD 修正空组列表假绿，复验全部现有组和 diff check；复核清理结果、入口与保留资产；识别已授权收尾漂移，不改旧 SHA256SUMS |
| B1 | T01 | 新增 product.json、policies、固定 schemas 和工具的 product/policy/io 模块；先定义合法/非法输入、模式与授权边界测试 |
| B2 | T02、T03 | 写五类核心 SKILL、保留 review-results 并补新引用测试；新增 cases.json 和最小 Python/JS fixture，先明确行为检查再增加工具功能 |
| B3 | T04 | task/evidence 模板、state 模块和 create/update/check 命令；测试身份串用、CAS 冲突、修改后失效、缺失证据和敏感数据处理 |
| B4 | T05 | 两端 adapter 模板及能力表；核实版本/入口，不提前将能力标为已验证 |
| B5 | T06 | build/package_check/owned_files、CLI 和两个发行包；覆盖资源闭包、可复现性、越界、用户修改、重复暂存、旧计划和中断 |
| B6 | T07 | prepare/collect/grade，实际执行宿主矩阵和必要原生对照；严重失败先修复再继续批量验收 |
| B7 | T08 | 英中入门、安装、升级、来源、支持矩阵和最小 CI；依据实际结果形成发布候选，不执行发布 |

工具代码按 TDD 实施，纯文档/技能文字采用结构检查及真实行为评估。可执行工具的覆盖率目标至少 80%，报告实际范围和无法覆盖项；覆盖率不证明模型过程或业务结果。

统一 Python 门禁通过 `tests/run_python_tests.py` 显式拒绝空测试集合，不依赖 Python 小版本对空 discover 的默认退出行为。构建先在同文件系统私有目录生成包，通过 package closure、接口与 reviewer 静态约束校验，再验证 ZIP 解包内容并发布；失败清除私有临时产物，保留原有空输出目录。Git dirty 断言使用明确的 clean/dirty fixture，不依赖开发工作区当前状态。

统一门禁注册汇总器自身测试、技能契约、所有新 Python 单元/集成测试及包检查。不得有空测试集合、未找到测试文件仍成功、用 stdout 的 Passed 数字代替退出状态等假绿。lint 使用项目内锁定的依赖，不为全绿关闭与本次实现相关的规则。

## BEL 迁移与旧来源退出

先写原来源到新文件的映射，迁入实际需要的 TDD、排查、验证、审查和自有文件保护行为。旧管理脚本中的全局 AGENTS 写入功能退出首版；保留适用的安全测试场景，用新接口验证对应保证。

一次性验收 fixture 和验证记录迁入 evals/fixtures 及注明历史状态的迁移说明，不能把历史 CLI 发现记成新产品验收。BEL 许可证保存在 LICENSES 和两端包中，原目录退出后仍能追溯。

仅在新核心来源、管理工具、包、引用和适用测试通过，且历史证据与许可证迁移完成后，删除仓库内已被替代的 zcode-workflow。真实宿主验收如果受阻，可以保留新实现但迁移说明必须注明限制；不卸载用户当前 BEL、Superpowers 或其他插件，不更改其全局规则。

## 完成定义和交付状态

实现完成要求 B1 至 B5 的代码、测试、包和管理工具均成立，B7 的文档准备完成，实际变更经过独立 diff Review 且确定严重问题已解决。验收完成还要求两个声明支持的宿主组合具备 T07 的真实证据。发布候选要求这两层都完成，并准备好对外支持说明。

T07 环境受阻时，交付标记为 implemented_with_acceptance_blocked，列出具体组合、命令/错误、已经完成的工作和后续验证方法；不能写全阶段完成或可发布。未知风险与确认缺陷分开，不能借环境阻塞隐藏实现失败。

完整开发 Prompt 可以一次确认本规格和 B0 至 B7 的执行范围。执行者拆步骤后持续完成，不因每批次的普通实现细节再次请求许可。实际全局安装、关闭现有插件、Git 操作和外部发布只有另有明确授权才执行。

本规格不会用一次指令保证所有运行时都可用；它要求实现者完成全部可执行工作，并准确保留无法完成的真实验收状态。
