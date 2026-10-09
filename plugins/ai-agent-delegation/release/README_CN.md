# Agent Delegation

独立派发插件首版候选。用户明确说“交给 Claude Code 实现”“交给 ZCode /
Codex 做”，或显式调用 agent-delegation 并指定任务与目标时，组织限定范围
并派发到独立 session，把准确 task/session、产物及验证结果收回发起会话。
三工具对等，不固定模型分工，不强制 review 流程。

普通开发、原生 subagent、讨论、引用内容及 Agent 自写 approved 标记不会
派发。同 engine 必须明确请求独立会话；指定目标不可用时报告原因，不替换。
续接准确 taskId，不用最近会话或 --last。

依赖 Python 3 与独立安装/配置的 agent-bridge/v1 CLI。包内薄客户端仅用
标准库编码参数、读取版本化 JSON 与记录最小回执。运行时、引擎驱动、任务
服务、状态和凭据由外置 Bridge 持有。插件不自动安装、不改全局配置、不提供
MCP server，不把自然语言识别或 source/approved flag 当作人类身份认证。

使用前阅读[技能](skills/agent-delegation/SKILL.md)、
[CLI 契约](skills/agent-delegation/references/bridge-client.md)、
[支持矩阵](docs/support-matrix.md)与[宿主验收方案](docs/host-evaluation.md)。
源码/fixture/包检查与真实宿主验收分别报告。三宿主加载、自然语言入口、
引擎执行、准确续接及桌面可见性保持 **unverified**；首版不声明原生 MCP。

Zack-Zz 是公开维护者署名，不代表平台认证。安装、Git 与发布需要各自用户
授权。当前为候选，不是已验收 stable 发行。许可证：[MIT](LICENSE)。
