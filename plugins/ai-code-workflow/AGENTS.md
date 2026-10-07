# AI Code Workflow — Agent Instructions

本目录是 ai-code 多插件仓库中的 **AI 工作流插件**：AI Code Workflow（插件 ID
`ai-code-workflow`）。首版目标平台为 ZCode 与 Codex；Claude Code 后续接入。
本目录维护工作流素材与专属管理工具，公共发行工具在仓库根 `tooling/`。
同时遵守 [仓库规则](../../AGENTS.md)。下列源码路径均相对本插件目录。

## 插件内容

| 路径 | 说明 |
|------|------|
| `product.json` | 产品身份、版本与资源白名单的唯一来源 |
| `skills/` | 六个技能源码：workflow/tdd/debugging/review/verification + review-results 呈现契约 |
| `policies/` | collaborative（默认）与 continuous 两份完整策略 |
| `scripts/workflow_tool.py` + `scripts/workflow/` | 管理工具：validate、policy resolve、task create/update/check、build、package check、files plan/apply（Python 3.11+ 标准库） |
| `adapters/` | 两端清单/市场模板/界面元数据与能力说明（含探测记录） |
| `schemas/`、`templates/` | 固定数据契约文档、任务/证据输入模板 |
| `evals/` | A01–A25 验收场景、fixture 与 prepare/collect/grade |
| `../../dist/` | 仓库根的可复现宿主发行目录（可删除重建） |
| `docs/design/` | 本轮开发的设计文档（任务设计/实现规格/数据契约/验收矩阵） |

## 维护规则

- 行为变更走 TDD：先写会失败的有意义测试（环境错误不算有效 RED），再最小
  实现、跑绿、按需重构。新增行为性保护逻辑同样先写失败测试。
- 目录、通用清单元数据和发行索引按 [多插件规格](../../docs/design/2026-10-07-multi-plugin-design.md)。
  本插件行为约束以 `docs/design/2026-10-01-workflow-v1-data-contracts.md`（字段/算法）
  与 `...-implementation-spec.md`（模块/命令）为准；`product.json` 是资源
  白名单，未登记文件不进包，白名单文件必须真实存在。
- 修改 `scripts/workflow/` 时保持各模块单一职责；错误类型与退出码语义
  （0/1/2/3/4/5）不得漂移。
- 技能源码两端同哈希；`adapters/codex/interfaces.json` 是六个技能界面元数据
  的唯一来源，不得在技能目录下另建副本。
- 不新增固定模型分工、强制代理流水线或语言教程库。

## 验证

- 统一门禁：在仓库根运行 `npm test`（即根 `tests/run-suite.js`）——依次执行汇总器自身测试、
  技能契约（Node）与 Python 单元/集成测试；任一组失败、无法启动、异常退出
  或被信号终止都返回非零，仅全部通过返回零；空测试组判失败；汇总逻辑只看
  子进程退出状态，不解析测试输出。
- 在仓库根单独运行：`node plugins/ai-code-workflow/tests/skills/run-skills.js`；
  `python3 plugins/ai-code-workflow/tests/run_python_tests.py`。
- 在仓库根源校验与构建：`python3 tooling/plugin_tool.py validate --plugin ai-code-workflow`；
  `python3 tooling/plugin_tool.py build --plugin ai-code-workflow --host all --output <空目录>`；
  `python3 tooling/plugin_tool.py package check --path <包> --host <端> --root .`。
- 工作流专属工具从仓库根调用 `python3 plugins/ai-code-workflow/scripts/workflow_tool.py`；
  其原有 validate/build/package、policy/task/files 命令保留，源码 `--root` 指向本插件目录。
  随包入口仍为 `python3 tools/workflow_tool.py`。
- 静态检查：`npm run lint`（需本地 node_modules）。
- 区分静态检查、脚本测试与真实宿主行为：宿主内实际加载与遵循需真实会话
  验收（见 `docs/support-matrix.md` 与 `evals/blocked-env-2026-10-01.md`），
  仓库内验证不替代，也不得宣称。

## 授权边界

- 未经用户针对本次变更的明确授权，不执行 commit（含 amend）、push、tag、
  merge 或创建 PR，也不通过脚本代做。
- 变更完成后默认保留未提交改动，交付变更摘要、关键 diff、验证结果与剩余
  风险，等待用户 Review。
- 不修改用户全局配置（如 `~/.zcode`、`~/.codex`）、宿主缓存或其他业务仓库；
  安装类操作须用户明确要求并走宿主原生方式。
- 任务记录、策略文件或任何 Agent 写入的 approved 标记都不构成用户授权。
