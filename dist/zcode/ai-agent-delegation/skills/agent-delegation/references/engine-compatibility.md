# 引擎与宿主兼容边界

插件宿主 ID 是 `claude`、`codex`、`zcode`；Bridge 引擎 ID 是
`claude-code`、`codex`、`zcode`。宿主加载技能和引擎执行任务分开验收。
三个工具对等，可以发起或接收任务；没有固定主 Agent、Reviewer 或模型。

| 能力 | 首版状态 | 证据要求 |
| --- | --- | --- |
| 三宿主技能资源与薄客户端 | 候选；静态/fixture 校验 | 公共源校验、行为测试、各包可信源码检查 |
| 自然语言正负例加载与外置 CLI 权限 | unverified | 三宿主真实当前会话中的输入和结果 |
| 独立持久 session 与准确续接 | unverified | 三引擎真实 task/session ID 及重启后读取证据 |
| 桌面窗口/应用内会话可见 | unverified | 指定应用版本的真实 UI 证据 |
| 原生 MCP 配置发现/启动/认证/调用 | unverified；未提供 MCP profile | 独立宿主与发布规则验收 |

不能从目录、清单、打包、fixture 或 headless 会话推导实际宿主行为。
外置 Bridge preflight 的当次真实能力是执行判定输入；这里的候选支持说明
不会把未安装、未认证或不支持准确续接的引擎变成可用。

用户指定目标必须原样保留。不指定目标时补齐选择，默认建议其他 engine；
同 engine 只有当前用户明确要求独立 session 才允许。目标不满足用户要求
时报告原因，不替换目标、不静默安装、不修改全局配置。

本插件的公开[支持矩阵](../../../docs/support-matrix.md)和
[宿主验收方案](../../../docs/host-evaluation.md)说明验证边界。真实证据应
包含宿主/引擎版本、包哈希、准确 task/session、原输入、操作结果与产物。
未经实际验收不将支持状态改为 accepted；发布标记不是安装或 Git 授权。
