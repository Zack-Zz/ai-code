# ai-code — Agent Instructions

本仓库承载多个面向公开发布的 **AI 相关插件**。当前首个插件为 CodeVow
（ID `ai-code-workflow`），源码位于 `plugins/ai-code-workflow/`；插件行为、
测试和支持声明由各插件维护。
公共层负责插件注册、源校验、构建、包检查、临时开发市场、main 公开快照
及三宿主发布准备。

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
| `docs/design/2026-10-07-multi-plugin-design.md` | 多插件改造规格与执行顺序 |
| `published/` | 正式发行记录、当前指针、所有权回执与固定 Codex 安装内容 |
| `dist/` | 被忽略的本地/CI 临时构建输出，不进入 Git 跟踪 |

## 维护规则

- 修改目标插件前读取其 `AGENTS.md`；workflow 的行为规则只约束该插件。
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
  自由组合 mode/prerelease。历史 numeric Prerelease 保留原记录和字节。
- 源码与公开市场统一使用 main，每个插件 ID 只有一个当前正式入口；
  preview 只公开 Release，不更新市场。没有正式版的插件不回退到 preview。
  `product.json` 是开发权威，`published/` 是已上线来源，允许版本不同。
- `dist/` 不得进入新提交或远端分支，CI 拒绝任何跟踪文件。公开 ZIP 是
  Release 附件；`published/codex/` 仅保存正式宿主安装所需的固定目录。
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
- `release check/prepare/verify` 区分 draft 与 stable；stable 必须通过干净
  Git、规范标签和全部声明宿主的字节绑定验收。GitHub Draft 是公开状态，
  不等于本地验收 mode；新发行公开前须回读完整附件并复核冻结源码标签。
- 默认本地验收读取实际私有材料；`release acceptance-export` 全部核验后
  只导出哈希声明，维护者审核并随源码标签冻结。Actions 显式使用 committed
  验收，重验摘要 HEAD 字节、公开输入与所有包哈希，不读取或公开私有正文。
  摘要是维护者事实声明，不是平台认证或发布授权，不可手写以绕过验收。
- `marketplace sync --output <空目录>` 仅生成临时开发市场；
  `marketplace check` 只读核验公开快照、冻结源码 S 与固定分发提交 D。
  `marketplace initialize --migrate` 仅在旧根清单精确匹配 ownership 回执时
  迁为空正式快照，拒绝未知内容、人工编辑及链接。
- Release 的 Prepare 与测试只读；Publish 经 main 的 plugin-release 审核，
  正式成功后显式调用 Sync。市场 plan 只读，deploy 经 plugin-marketplace
  审核后按已审阅哈希及 main 基础 SHA 写入，不接受 absent 或 force push。
  本地工作流验证不等于远端执行、环境权限或真实宿主升级通过。

## 授权边界

- 未经用户针对本次变更的明确授权，不执行 commit（含 amend）、push、tag、
  merge 或创建 PR，也不通过脚本代做。
- 变更完成后默认保留未提交改动，交付摘要、关键 diff、验证结果与剩余风险，
  等待用户 Review。
- 不修改用户全局配置（如 `~/.zcode`、`~/.codex`）、宿主缓存或其他业务仓库；
  安装类操作须用户明确要求并走宿主原生方式。
- 任务记录、策略文件或任何 Agent 写入的 approved 标记都不构成用户授权。
