---
description: 从会话提取可复用模式，在保存前先做质量自评，并决定保存到全局还是项目目录。
---

# /learn-eval - 提取、评估、再保存

**Tool Scope:** `claude` / `codex` / `kiro`

这是 `/learn` 的增强版：在写入 skill 文件前增加质量门禁和保存位置决策。

## 提取目标

重点关注：

1. 错误修复模式：根因 + 修复 + 可复用性
2. 调试技巧：不直观步骤、工具组合
3. 规避方案：库缺陷、API 限制、版本特定修复
4. 项目特定模式：约定、架构决策、集成模式

## 流程

1. 回顾会话，找可提取模式
2. 选出最有价值、最可复用的一条
3. 决定保存位置：
   - 问题：这个模式是否适用于其他项目？
   - 全局：`$AI_CODE_HOME/skills/learned/`（跨项目通用）
   - 项目：当前项目 `.claude/skills/learned/`（强项目相关）
   - 不确定时优先全局（全局迁到项目更容易）
4. 按模板草拟 skill 文件：

```markdown
---
name: pattern-name
description: "Under 130 characters"
user-invocable: false
origin: auto-extracted
---

# [Descriptive Pattern Name]

**Extracted:** [Date]
**Context:** [Brief description of when this applies]

## Problem
[What problem this solves - be specific]

## Solution
[The pattern/technique/workaround - with code examples]

## When to Use
[Trigger conditions]
```

5. 保存前自评（rubric）：

| 维度 | 1 | 3 | 5 |
|------|---|---|---|
| Specificity | 只有抽象原则，无代码示例 | 有代表性示例 | 示例丰富，覆盖主要用法 |
| Actionability | 不知道具体怎么做 | 主步骤可执行 | 可直接落地，边界场景清晰 |
| Scope Fit | 过宽或过窄 | 基本匹配，边界略模糊 | 名称、触发条件、内容完全匹配 |
| Non-redundancy | 与已有 skill 高度重复 | 有重叠但仍有增量 | 价值明显独特 |
| Coverage | 只覆盖一小部分 | 覆盖主场景，缺常见变体 | 主场景、边界和陷阱都覆盖 |

- 每项打分 1-5
- 任一项 ≤2 必须先改稿，再评估，直到全部 ≥3
- 向用户展示评分表和最终草稿

6. 请求用户确认：
   - 展示：拟保存路径 + 评分表 + 最终草稿
   - 必须等用户明确确认后再写入

7. 保存到最终路径

## 第 5 步输出格式（评分表）

| 维度 | 分数 | 理由 |
|------|------|------|
| Specificity | N/5 | ... |
| Actionability | N/5 | ... |
| Scope Fit | N/5 | ... |
| Non-redundancy | N/5 | ... |
| Coverage | N/5 | ... |
| **总分** | **N/25** | |

## 注意事项

- 不提取琐碎修复（拼写、简单语法错误）
- 不提取一次性问题（临时 API 故障等）
- 优先提取能在未来节省时间的模式
- 一个 skill 只表达一个模式
- Coverage 低时，先补常见变体再保存
