# CodeVow · AI 编码工作流

[English](README.md) | 简体中文

CodeVow 是面向公开发布、可跨宿主移植的 AI 编码助手工程工作流：**先确认计划再开发、
测试先行、证据驱动排查、聚焦风险的审查、绑定最终代码状态的验证**。
候选包目标为 Claude Code、Codex 与 ZCode；三端真实宿主验收均为 unverified。

同一份源码生成三个宿主的发行包。包内含六个技能——`workflow`、`tdd`、
`debugging`、`review`、`verification` 与共用审查呈现契约 `review-results`——
以及两种协作策略（默认 `collaborative`；`continuous` 仅调整节奏）、任务/证据
记录工具和带回执的文件暂存。不含自有 Agent 运行时、MCP 调度、后台服务、
模型路由或强制多角色流水线。

**历史验证基线（2026-10-03）：2.0.0 未发布候选产物，implemented_with_acceptance_blocked。** 已实现并通过确定性测试，
七个核心工具模块的语句覆盖率均超过 80% 目标；真实宿主验收
在开发机上受环境阻塞，能力一律如实标注 `unverified`——见
[docs/support-matrix.md](docs/support-matrix.md) 与
[evals/blocked-env-2026-10-02.md](evals/blocked-env-2026-10-02.md)。
在任何机器上完成真实会话验收之前，请勿声称本产品已被宿主验证。

2026-10-07，展示名由 AI Code Workflow 更为 CodeVow。插件 ID
`ai-code-workflow` 保持；CodeVow 的初始版本定为 `1.0.0`，此前 `2.0.0` 为
安装前的工程候选编号。早期设计和验证记录保留当时的版本、名称与日期，
版本重新编号不增加真实宿主验收声明。

本目录是 [ai-code 插件集合](../../README.zh-CN.md) 中的一个插件。除明确注明
从仓库根执行的命令外，本文路径均相对本插件目录。公共构建与新插件接入见
[作者指南](../../docs/plugin-authoring.md)。

## 当前候选元数据

publisher 声明在 product.json 维护，不代表身份认证。包内提供 PNG 发布图标和 SVG 备用标识
与可移植中英文 README；release.json 选择说明、草稿发行备注和验收证据。
Claude Code、Codex、ZCode 三个证据槽当前均为 null，草稿构建不能晋升为稳定版。

Claude Code 与 ZCode 的 Reviewer 使用同一份共享职责正文，声明只读工具、
继承模型和最多十二轮；实际限制是否生效仍未验证。现有 A25 是历史 Codex/
ZCode 两端矩阵，不能将其结果用作新增 Claude 目标的验收证据。

## 你得到什么

- **先计划后实施**：每个开发任务（含 QUICK 与紧急修复）都有相称的计划并
  等待你的确认；已确认的范围不重复询问。continuous 只在已授权范围内改变
  节奏，切换模式本身不构成任何授权。
- **真实 TDD**：有效 RED（环境故障不算）、最小 GREEN、在既有基线下重构。
- **证据驱动排查**：显式假设与最小区分性实验；连续两次无证据尝试即停止猜测。
- **诚实审查**：只查受影响维度；critical 风险尝试独立只读 Reviewer；主 Agent
  核实发现；最终输出走 review-results 的结论先行契约。
- **不腐烂的验证**：完成声明绑定最终代码状态；代码变化使旧通过记录失效；
  未解决的 critical/high 缺陷让任务保持未完成。
- **可审计且不泄漏权限**：可选的任务/证据记录，CAS 更新与内容哈希失效判断；
  记录永不生成用户授权。

## 快速开始

当前为自建市场试用候选，真实宿主验收未完成。以下命令在 ai-code 仓库根目录执行：

```sh
npm test
python3 tooling/plugin_tool.py validate --plugin ai-code-workflow
python3 tooling/plugin_tool.py build --plugin ai-code-workflow --host all --output dist-check
python3 tooling/plugin_tool.py package check \
  --path dist-check/zcode/ai-code-workflow --host zcode --root .
```

安装构建产物到 Claude Code/Codex/ZCode：[docs/installation.md](docs/installation.md)。
日常使用与策略：[docs/usage.md](docs/usage.md)。
自建市场分发：[发布准备](../../docs/publishing.md)。
插件源码入口仍为仓库根目录下的
`plugins/ai-code-workflow/scripts/workflow_tool.py`，安装包入口仍为
`tools/workflow_tool.py`；policy/task/files 行为属于该插件。插件 ID 和候选版本
为 `ai-code-workflow` 与 `1.0.0`。

## 插件目录结构

| 路径 | 用途 |
|---|---|
| `skills/`、`policies/`、`product.json` | 工作流源码与产品身份/资源白名单 |
| `scripts/workflow_tool.py`、`scripts/workflow/` | 管理工具（validate/policy/task/build/package/files），仅 Python 3.11+ 标准库 |
| `adapters/claude/`、`adapters/codex/`、`adapters/zcode/` | 三端原生清单、市场模板、Reviewer 声明和界面元数据 |
| `assets/`、`release/`、`release.json` | PNG/SVG 图标、可移植包说明、草稿备注与验收槽 |
| `schemas/`、`templates/` | 固定数据契约文档与任务/证据输入模板 |
| `evals/` | A01–A25 验收场景、一次性 fixture、prepare/collect/grade 工具 |
| `../../dist/` | 仓库根目录生成的宿主发行目录（可随时重建） |
| `docs/` | 设计文档、使用、安装、迁移、支持矩阵、覆盖率 |
| `tests/` | 插件 Node 契约检查和 Python 单元/集成测试；统一门禁在 `../../tests/run-suite.js` |

## 验证与开发

- 统一门禁：`npm test`（`tests/run-suite.js`）——任一组失败其余组仍执行；
  只依据子进程退出状态判定（不解析输出）；空测试组判失败。
- 仓库根目录运行 workflow Python：`python3 plugins/ai-code-workflow/tests/run_python_tests.py`。
- 公共工具 Python：`python3 tests/run_python_tests.py`。
- 仓库根目录单独运行技能契约：`node plugins/ai-code-workflow/tests/skills/run-skills.js`。
- 静态检查：`npm run lint`（eslint + markdownlint，需先 `npm install`）。
- 覆盖率方法与数字：[docs/coverage.md](docs/coverage.md)。
- 从 backend-engineering-lite 迁移：[docs/migration.md](docs/migration.md)。

## 许可证与来源

MIT——见 [LICENSE](LICENSE) 与 [NOTICE](NOTICE)。本仓库早期历史派生自
Affaan Mustafa 的 ai-code（MIT）；v1 工作流迁移自 backend-engineering-lite
（同为本仓库历史），其许可证保留在
[LICENSES/backend-engineering-lite.txt](LICENSES/backend-engineering-lite.txt)
并随每个发行包分发。BEL 的 README 致谢 obra/Superpowers 的工作流思想启发；
未复制其源码。
