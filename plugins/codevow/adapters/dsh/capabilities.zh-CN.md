# DeepSeek Harness 能力边界

[English](capabilities.md) | 简体中文

候选 bundle 以已发布的 `0.2.1-rc.2` API 为目标。设计最初参考固定上游提交
`22ddee3792402c3e70ec5f86a63c3e3e895a2f60`；实际 RC2 使用官方
`agent-tool-presentation(mode: native)`，spawn 配置使用 `modelSelectionSettings: false`。Web profile 必须提供 agentPresets、agents、tools、
systemPrompt、subagents spawn 与 sessionProjections。缺依赖由原生 Loader 报告，不降级。

`workflow_reviewer` 选择 `codevow-reviewer`；模型路由继承父级，不开放其他 preset。
共享合同在构建时生成 JSON 字符串。原生 read/grep/glob、Agent 自身 scope 限制和
composition scope 最终 guard 共同约束工具。搜索可启动固定参数 ripgrep，但无通用 shell。
文件读取根沿用宿主配置；reviewer_restriction 与 workspace_isolation 分别验收。
创建时失败不会放行排队工作；重组、恢复、销毁与卸载均有生命周期处理。

单元契约和包完整性不代表原生激活、模型行为、安装或生命周期验收；四端 acceptance
保持 null。随包 Python 工具仍要求 Python 3.11+。
