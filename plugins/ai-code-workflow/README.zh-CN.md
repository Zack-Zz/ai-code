# CodeVow · AI 编码工作流

[English](README.md) | 简体中文

CodeVow 帮助 AI 编码助手把需求变成有计划、经过测试和审查的代码变更。
它为 Claude Code、Codex 和 ZCode 提供先计划后开发、测试先行、证据驱动排查
和最终状态验证的工作方式。插件 ID 为 `ai-code-workflow`。

## 安装与开始使用

按[安装指南](../../docs/installation.zh-CN.md)注册市场、选择 CodeVow 并安装、启用，
可安装插件以市场列表为准。指南还提供 Release 下载、更新和卸载步骤。

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
