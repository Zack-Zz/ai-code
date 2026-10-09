# ai-code 文档导航

更新：2026-10-09（Asia/Shanghai）。仓库公共机制与各插件自己的设计、支持证据分开维护。

## 总体架构与新插件设计

- [多插件总体架构](architecture.md)：公共注册/构建/发行层、独立插件与 ai-mcp 技术模块的责任边界。
- [Agent 派发插件设计](design/2026-10-08-agent-delegation-plugin-design.md)：独立候选插件；明确用户派发、三执行器、独立会话、接口与场景验收。
- [本轮实现与验证记录](reviews/2026-10-08-agent-delegation-implementation.md)：已实现范围、公共发布衔接和实际宿主证据边界。
- [Bridge开发收口](../../ai-mcp/docs/reviews/2026-10-09-agent-bridge-development-delivery.md)：默认Codex会话协议、停止证明、ZCode入口限制及本次review/Git交付。
- [ai-mcp 架构](../../ai-mcp/docs/architecture.md)与[Bridge 模块设计](../../ai-mcp/docs/modules/agent-bridge.md)：技术执行、CLI/MCP/API 和状态的维护方。

## 当前公共机制

- [插件作者指南](plugin-authoring.md)：独立身份、资源闭包、宿主适配、注册、测试与验证边界。
- [发布指南](publishing.md)、[发行证据契约](release-evidence.md)：区分包准备、宿主行为、Git 与发布授权。
- [2026-10-07 多插件改造](design/2026-10-07-multi-plugin-design.md)、[三宿主发行设计](design/2026-10-07-three-host-release-mechanism.md)：保留历史方案；当前宿主范围结合作者指南及工具源码核对。
- [公共迁移验收](reviews/2026-10-07-multi-plugin-migration.md)、[提交前审阅](reviews/2026-10-07-multi-plugin-precommit-review.md)：各自日期的检查证据，不构成本轮新插件通过记录。

## 插件自己的内容

- [CodeVow 文档与入口](../plugins/ai-code-workflow/README.zh-CN.md)、[支持矩阵](../plugins/ai-code-workflow/docs/support-matrix.md)：仅适用于该插件，不能作为其他插件的运行契约。
- [Agent Delegation](../plugins/ai-agent-delegation/README.md)：0.1.0 候选已登记；完整三宿主派发闭环和安装/正式发布未验收，未提供原生 MCP 清单。
