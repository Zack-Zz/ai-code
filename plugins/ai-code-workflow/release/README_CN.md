# CodeVow · AI 编码工作流

[English](README.md) | 简体中文

CodeVow 帮助 AI 编码助手把需求变成有计划、经过测试和审查的代码变更。
它为 Claude Code、Codex 和 ZCode 提供先计划后开发、测试先行、证据驱动排查
和最终状态验证的工作方式。插件 ID 为 `ai-code-workflow`。

## 安装与开始使用

按[安装指南](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.zh-CN.md)注册市场、选择 CodeVow 并安装、启用，
可安装插件以市场列表为准。指南还提供 Release 下载、更新和卸载步骤。

开启新会话，说明目标、范围和验收条件，例如：

> 新增批量折扣档位，保持现有定价行为不变，测试档位边界。先给我计划，再实施。

也可以直接请求排查或审查：

> 结合日志和代码定位偶发超时，先查原因。
>
> 审查这次 diff，重点看权限和数据一致性风险。

## 核心工作方式

| 技能 | 用途 |
|---|---|
| `workflow` | 澄清需求，确认与任务规模相称的计划，组织后续工作 |
| `tdd` | 行为变更先写有意义的失败测试，再实现和重构 |
| `debugging` | 用明确假设和小范围实验定位原因 |
| `review` | 审查受影响风险并核实发现，按需要尝试独立审查 |
| `verification` | 检查最终代码状态，如实报告验证结果 |
| `review-results` | 先给审查结论，再说明影响和可点击的证据 |

只读问题保持只读。默认 `collaborative` 模式在确认开发计划后实施，已确认的
范围不重复询问。`continuous` 模式在你已明确授权的范围内持续推进。

两种模式都保留既有改动。提交、推送、打标签、合并、创建 PR、安装和对外发布
分别需要你明确授权；切换模式或写入任务记录不会产生授权。

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

默认配置来自 [collaborative](policies/collaborative.json) 或
[continuous](policies/continuous.json)。项目配置覆盖默认值，会话中明确给出的
选项优先。[使用指南](https://github.com/Zack-Zz/ai-code/blob/main/plugins/ai-code-workflow/docs/usage.zh-CN.md)介绍完整字段、配置查看、可选任务记录
和项目文件暂存。

插件使用你已有的宿主、账号和所选模型。Markdown 技能无需额外 Node.js 或
Python。可选工具需要 Python 3.11+；文件暂存需要支持 POSIX 文件操作的平台。
Python 工具不联网、不调用模型、不执行 Git 操作。

## 更多帮助与许可证

- [安装、更新和卸载](https://github.com/Zack-Zz/ai-code/blob/main/docs/installation.zh-CN.md)
- [日常使用与高级工具](https://github.com/Zack-Zz/ai-code/blob/main/plugins/ai-code-workflow/docs/usage.zh-CN.md)
- [工作流规则](skills/workflow/SKILL.md)与[策略 Schema](schemas/policy.schema.json)

MIT，见 [LICENSE](LICENSE)、[NOTICE](NOTICE) 与保留的
[backend-engineering-lite 许可证](LICENSES/backend-engineering-lite.txt)。
CodeVow 工作流演进自本仓库中的 backend-engineering-lite；仓库早期历史派生自
Affaan Mustafa 的 ai-code。
