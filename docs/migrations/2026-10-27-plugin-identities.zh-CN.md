# 插件身份迁移 — 2026-10-27

[English](2026-10-27-plugin-identities.md) | 简体中文

当前源码变更尚未正式发布。请等宿主刷新后的 `ai-code` 市场出现新 ID，再卸载
仍可使用的旧安装。

| 旧 ID | 新 ID | 候选版本 | 展示名称 |
| --- | --- | --- | --- |
| `ai-code-workflow` | `codevow` | 2.0.0 | CodeVow |
| `ai-code-stack-standards` | `codestack` | 0.2.0 | CodeStack |

1. 使用宿主原生插件管理卸载旧 ID。
2. 刷新现有 `ai-code` 市场；市场名称与来源不变。
3. 安装并启用 `codevow` 和/或 `codestack`，开始新会话。
4. 核对版本与技能目录。保留项目 `.ai-workflow/` 中的策略、任务和证据，
   本次迁移不更改该目录。

只需重新安装插件，编码助手本身不变。新旧插件提供相同技能名，应先移除旧安装。
`workflow`、`code-standards` 等技能名保持不变。旧会话恢复依赖宿主行为，
不承诺无感续接。

旧 Release、标签、附件、固定安装提交和历史记录保持不变。发布工具只在新 ID
完成验证并激活的同一次市场更新中退役对应旧 ID。发布失败时保留旧市场入口。
本项目不提供自动卸载器、安装别名或缓存改写。DeepSeek Harness 是新增宿主，
没有旧 DSH ID 需要卸载。

操作见[安装指南](../installation.zh-CN.md)与[发布指南](../publishing.zh-CN.md)。

可选文件工具的暂存/回执命名空间随产品 ID 更新。旧文件计划保留，但应用前需
使用新工具重新生成；新插件不会静默认领旧身份的文件计划。
