# ai-code — Agent Instructions

本仓库承载多个面向公开发布的 **AI 相关插件**。当前首个插件为 CodeVow
（ID `codevow`），源码位于 `plugins/codevow/`；插件行为、
测试和支持声明由各插件维护。
公共层负责插件注册、源校验、构建、包检查、临时开发市场、main 公开快照
及四宿主发布准备。

## 仓库内容

| 路径 | 说明 |
|------|------|
| `catalog.json` | 插件目录注册表，只登记相对路径 |
| `distribution.json` | main、单市场身份、latest-stable 策略及宿主运输方式 |
| `plugins/<id>/product.json` | 该插件身份、版本、宿主与资源白名单的唯一来源 |
| `plugins/<id>/` | 插件源码、适配、文档、测试和局部 AGENTS 规则 |
| `tooling/plugin_tool.py`、`tooling/` | 通用校验、构建、包检查、市场同步与 release 工具 |
| `tests/` | 公共工具测试、插件测试汇总与统一门禁 |
| `docs/plugin-authoring.md` | 最小接入要求与验证边界 |
| `docs/publishing.md`、`docs/release-evidence.md` | 发布机制、渠道和证据契约 |
| `.agents/skills/ai-code-plugin-release/` | 本项目插件制作、验证与发布技能，不进入插件发行包 |
| `docs/design/2026-10-07-multi-plugin-design.md` | 多插件改造规格与执行顺序 |
| `published/` | 正式发行记录、当前指针、所有权回执与固定 Codex 安装内容 |
| `dist/` | 被忽略的本地/CI 临时构建输出，不进入 Git 跟踪 |

## 项目技能入口

- 在本仓库新增或维护插件、准备版本与发布说明、验证发行包，或处理构建/
  发布任务时，先读取
  [ai-code-plugin-release](.agents/skills/ai-code-plugin-release/SKILL.md)，
  再按当前任务读取其中链接的制作、发布或证据指南。
- 即使宿主没有自动发现项目技能，也按该入口读取；普通业务编码和插件用户
  的安装/使用问题不触发此维护流程。技能保留当前任务的用户授权，不把咨询、
  commit/push、实际发布或安装相互推导为授权。

## 维护规则

- 修改目标插件前读取其 `AGENTS.md`；workflow 的行为规则只约束该插件。
- 用户 README 说明当前项目、安装与用法；开发与发布流程各自进入专门指南。
  当前操作文档只说明最新接口，不加入旧版本兼容步骤；带日期的历史报告保留原记录。
- 面向外部读者的 README、安装、使用、配置及其他公开说明必须中英双语，
  默认英文，顶部提供双向语言切换；双语文档的内部链接保持所选语言。
- 设计、实现、验证记录和内部维护资料可以仅用中文，不要求全部翻译；
  已有译文可以保留，历史资料保留原语言和记录。
- 根 README 聚焦本项目。跨仓库关系在架构文档描述，安装依赖在对应插件指南说明。
- 行为变更走 TDD：先写有意义的失败测试，环境错误不算有效 RED；再最小
  实现、跑绿、按需重构。新增行为性保护逻辑同样先写失败测试。
- `catalog.json` 不复制插件 ID、版本或资源；根 private `package.json`
  不作为插件版本来源。不登记的插件不进入发行构建。
- 入包资源以插件清单的显式白名单为准。拒绝目录逃逸、符号链接、资源目标
  冲突、未登记活动文件和缓存入包；包检查独立重算实际文件与哈希。
- 公共工具不强制 workflow 的技能、策略、Reviewer 或 `.ai-workflow`
  任务状态。各插件保持独立身份、版本、资源闭包和源码哈希。
- 同一插件的共同资源在不同宿主包中保持同哈希；适配及生成资源单独声明。
- 新公开版本只接受 `X.Y.Z` 或 `X.Y.Z-preview.N`，数字无前导零；统一按
  数字比较 preview 序号，同核心正式版在其后。发行种类从版本派生，不能
  自由组合 mode/prerelease。
- 源码与公开市场统一使用 main，公开市场名统一为 `ai-code`；
  每个插件 ID 只有一个当前正式入口；
  preview 只公开 Release，不更新市场。没有正式版的插件不回退到 preview。
  `product.json` 是开发权威，`published/` 是已上线来源，允许版本不同。
- `dist/` 不得进入新提交或远端分支，CI 拒绝任何跟踪文件。公开 ZIP/TGZ 是
  Release 附件；`published/codex/` 与 `published/dsh/` 仅保存正式宿主安装所需的固定目录。
- 不提前增加运行时、SDK、调度、任意代码 hook、插件依赖管理、自动安装器、
  固定模型分工或强制代理流水线。新插件形态有实际需求后单独设计。
- publisher 只维护公开署名，不代表平台认证。release 配置不复制版本；
  原始验收材料不入公开包，证据标记不构成安装、Git 或发布授权。
- 保留历史报告的日期、命令和证据。迁移目录不会使历史验证成为本轮通过；
  更新当前操作导航时清楚区分历史基线与现行契约。

## 验证

- 统一门禁为仓库根目录 `npm test`（`tests/run-suite.js`），覆盖汇总器自身、
  公共工具及已注册插件测试。按 catalog 发现插件 `tests/skills/run-skills.js`
  或 `tests/run_python_tests.py`，每个正式插件至少一个；各组独立子进程运行，
  不加载任意测试命令 hook。任一组失败、无法启动、异常退出或被信号终止
  都返回非零；空测试组判失败；汇总只看退出状态，不解析输出。
- 公共源校验：`python3 tooling/plugin_tool.py validate --all`；也可使用
  `--plugin ID` 定向校验。
- 构建：`python3 tooling/plugin_tool.py build --all --host all --output <空目录>`。
- 包检查：`python3 tooling/plugin_tool.py package check --path <包> --host <端>
  --root <可信源码仓库>`；不能把待检查包当作自己的初始验证器。
- 公共工具 Python：`python3 tests/run_python_tests.py`；技能及局部测试入口见插件
  文档。静态检查为 `npm run lint`，需本地 node_modules。
- 区分静态校验、脚本测试、包完整性与真实宿主行为。原生加载、自动调用、
  运行工具或 MCP 的支持必须有实际宿主证据，不从清单或目录布局推导。
- `release prepare-version` 是 AI 本地辅助：用户给版本与改动说明，AI 起草
  中英正文并先预览、再应用版本与说明变更；旧证据失效时明确列出引用重置
  与有效生成摘要移除，保留私有材料和发布历史。不自动执行 Git、构建、发布
  或安装；完成后等待用户 Review 与针对本次 commit/push 的明确授权。
- `release check/prepare/verify` 区分 draft 与 stable；stable 技术就绪要求
  干净 Git、规范标签、有效公开输入与独立包校验，真实宿主验收独立报告。
  null/pending 不阻断技术发布，不能据此声称宿主通过。GitHub Draft 是公开
  状态，不等于本地验收 mode；公开前后须回读完整附件并复核冻结源码标签。
- 已提供的本地验收记录须读取实际私有材料并严格核验；可选的
  `release acceptance-export` 仍要求全部宿主真实验收，通过后只导出哈希
  声明，维护者审核并随源码标签冻结。Actions 显式使用 committed 模式；
  有摘要时重验 HEAD 字节、公开输入与所有包哈希，没有摘要与证据引用时
  保持 pending。不读取或公开私有正文，不因坏摘要回退或忽略。摘要是维护者
  事实声明，不是平台认证或发布授权，不可手写以绕过验收。
- `marketplace sync --output <空目录>` 仅生成临时开发市场；
  `marketplace check` 只读核验公开快照、冻结源码 S 与固定分发提交 D。
  不手工修改公开清单，正式市场更新通过受审核的计划与部署流程执行。
- 唯一手动发行入口为 main 的 Build & publish plugins / 构建与发布插件，
  只选择 plugin 与 operation=build|publish，版本和说明读取 product/release
  源码，规范标签自动派生。build 完整构建与复验，不远端写入；publish 经
  plugin-release 环境创建或复用不可变标签、回读附件并公开 Release，正式版
  自动调用内部市场工作流，preview 只公开 Release。市场 plan 只读，deploy
  经 plugin-marketplace 环境按本次生成的计划哈希及 main 基础 SHA 写入；
  环境若配置审核人，运行暂停等待批准，不接受 absent 或 force push。
  同版本不同公开字节拒绝；市场失败可按相同未变版本重跑 publish 继续同步。
  本地工作流验证不等于远端执行、环境权限或真实宿主升级通过。

## 授权边界

- 未经用户针对本次变更的明确授权，不执行 commit（含 amend）、push、tag、
  merge 或创建 PR，也不通过脚本代做。
- 变更完成后默认保留未提交改动，交付摘要、关键 diff、验证结果与剩余风险，
  等待用户 Review。
- 不修改用户全局配置（如 `~/.zcode`、`~/.codex`）、宿主缓存或其他业务仓库；
  安装类操作须用户明确要求并走宿主原生方式。
- 任务记录、策略文件或任何 Agent 写入的 approved 标记都不构成用户授权。
