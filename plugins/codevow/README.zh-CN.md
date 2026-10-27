# CodeVow · AI 编码工作流

[English](README.md) | 简体中文

CodeVow `codevow` 1.0.6 已发布，旧插件 ID 已退役。
[已发布记录](https://github.com/Zack-Zz/ai-code/blob/main/published/index.json)
是可安装版本的权威来源，已发行快照保持不可变。

CodeVow 帮助 AI 编码助手把需求变成有计划、经过测试和审查的代码变更。
它为 Claude Code、Codex、ZCode 和 DeepSeek Harness 提供先计划后开发、测试先行、证据驱动排查
和最终状态验证的工作方式。插件 ID 为 `codevow`。

## 安装与开始使用

按[安装指南](../../docs/installation.zh-CN.md)注册市场、选择 CodeVow 并安装、启用，
可安装插件以市场列表为准。指南还提供 Release 下载、更新和卸载步骤。

按宿主选择安装路径：[Codex 桌面端与 CLI](../../docs/installation.zh-CN.md#codex)、
[Claude Code 桌面端与 CLI](../../docs/installation.zh-CN.md#claude-code)、
[ZCode 桌面端与 macOS 应用内置 CLI](../../docs/installation.zh-CN.md#zcode)，或
[DeepSeek Harness 桌面端与独立 npm CLI](../../docs/installation.zh-CN.md#deepseek-harness)。

开启新会话，说明目标、范围和验收条件，例如：

> 新增批量折扣档位，保持现有定价行为不变，测试档位边界。先给我计划，再实施。

也可以直接请求排查或审查：

> 结合日志和代码定位偶发超时，先查原因。
>
> 审查这次 diff，重点看权限和数据一致性风险。

技能描述帮助宿主选用技能；安装本身不保证先读取 `workflow`。
[项目入口指南](docs/usage.zh-CN.md#接入项目入口)提供编程相关任务的可选短指令，
由你通过已核对加载方式的宿主项目入口接入，并说明直接调用技能的授权检查
和实际宿主验证边界。

## 核心工作方式

| 技能 | 用途 |
|---|---|
| `workflow` | 澄清需求，确认与任务规模相称的计划，组织后续工作 |
| `tdd` | 行为变更先写有意义的失败测试，再实现和重构 |
| `debugging` | 用明确假设和小范围实验定位原因 |
| `review` | 审查受影响风险并核实发现，按需要尝试独立审查 |
| `verification` | 检查最终代码状态，如实报告验证结果 |
| `review-results` | 先给审查结论，再说明影响和可点击的证据 |

## 选择协作模式

根据你是否希望在助手动手修改前确认方案，选择模式：

| 模式 | 如何开始工作 | 适合什么时候用 |
|---|---|---|
| `collaborative` — 协作模式（默认） | 助手先调查、说明准备怎么改，等你确认方案后再动手修改。 | 你希望先看过方案，再开始实施。 |
| `continuous` — 连续执行模式 | 你明确要求实施任务后，助手简要说明计划，就在你授权的范围内继续完成。 | 目标和范围已经清楚，你希望助手直接推进到交付。 |

进入实施后，两种模式都会持续完成编码、测试和审查，无需你逐步批准普通操作。
已经确认过的方案会直接复用；范围或关键方案发生实质变化时，助手会就变动部分
重新确认。

两种模式的测试、审查和验证要求相同，都会保留你已有的改动。
仅询问或要求排查时，助手保持只读；已授权任务中的后续问句不会取消你已经
允许的工作。提交、推送、打标签、合并、创建 PR、安装和对外发布仍需要你
明确要求；切换模式或写入任务记录不会代替你的授权。

## 项目配置

在项目中创建 `.ai-workflow/policy.json`，设置偏好：

```json
{
  "schema_version": 1,
  "mode": "collaborative",
  "response_language": "zh-CN",
  "verification_notes": ["交付前运行相关测试"]
}
```

默认使用 `collaborative`。将 `mode` 改为 `continuous`，即可选择上面说明的
连续执行模式。项目配置覆盖随包默认值，会话中明确给出的
选项优先。[使用指南](docs/usage.zh-CN.md)介绍完整字段、配置查看、可选任务记录
和项目文件暂存。

插件使用你已有的宿主、账号和所选模型。Markdown 技能无需额外 Node.js 或
Python。可选工具需要 Python 3.11+；文件暂存需要支持 POSIX 文件操作的平台。
Python 工具不联网、不调用模型、不执行 Git 操作。

## 更多帮助与许可证

- [安装、更新和卸载](../../docs/installation.zh-CN.md)
- [日常使用与高级工具](docs/usage.zh-CN.md)
- [工作流规则](skills/workflow/SKILL.md)与[策略 Schema](schemas/policy.schema.json)

MIT，见 [LICENSE](LICENSE)、[NOTICE](NOTICE) 与保留的
[backend-engineering-lite 许可证](LICENSES/backend-engineering-lite.txt)。
CodeVow 工作流演进自本仓库中的 backend-engineering-lite；仓库早期历史派生自
Affaan Mustafa 的 ai-code。

## DeepSeek Harness

插件包与[自定义市场索引](https://raw.githubusercontent.com/Zack-Zz/ai-code/main/published/dsh/index.json)均已发布。
桌面端自带 Node.js 与 pnpm，无需另行安装 npm CLI。桌面端与独立 npm CLI 步骤见
[Harness 安装指南](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.zh-CN.md#deepseek-harness)。
已发行包的 `engines.dsh` 与 DSH peerDependencies 均精确锁定 `0.2.1-rc.2`；
桌面端 `0.2.1-rc.3` 尚未被当前声明覆盖。真实桌面端、实际加载、自动选择、长会话和
生命周期验收仍待完成，构建和包检查不能代替宿主验收。技能使用官方 `/workflow` 显式调用。两个插件通过各自的官方文件系统提供方读取包内资源，启停互不替代。

独立审查使用 `workflow_reviewer` 与 `codevow-reviewer` preset，仅允许 read/grep/glob。
目标 profile 必须提供 agentPresets、Agent/工具/提示词及 subagents spawn 服务；缺失时原生 Loader
报告无法激活，该 profile 不受完整支持。Python 辅助工具仍要求 Python 3.11+；缺 Python 时按技能
手工解析策略并披露未验证项。工具白名单不构成独立文件系统沙箱，读取根沿用宿主权限。

身份变更的卸载和重装步骤见[本次迁移说明](https://github.com/Zack-Zz/ai-code/blob/main/docs/migrations/2026-10-27-plugin-identities.zh-CN.md)。
