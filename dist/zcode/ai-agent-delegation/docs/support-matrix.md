# 支持矩阵

Agent Delegation 首版候选提供单技能、三宿主元数据与外置 Bridge 薄客户端。
身份、版本、宿主和资源白名单以 product.json 为唯一来源；公开署名是维护者
署名，不能解读为平台认证。

| 宿主 | 插件形态 | 自然语言加载 | CLI 派发/准确续接 | 桌面可见 | 原生 MCP |
| --- | --- | --- | --- | --- | --- |
| Claude Code (`claude`) | 技能包 | unverified | unverified | unverified | unverified；未提供 |
| Codex (`codex`) | skills-only + openai.yaml | unverified | unverified | unverified | unverified；未提供 |
| ZCode (`zcode`) | 技能包 | unverified | unverified | unverified | unverified；未提供 |

`allow_implicit_invocation: true` 允许 Codex 自然语言加载候选；不能证明宿主
实际选中了技能。普通开发/原生 subagent/讨论/引用负例必须与明确正例一起
验收。三工具既能发起也能成为目标；引擎 canonical ID 为 `claude-code`、
`codex`、`zcode`，host ID 与 engine ID 不混用。

本地子进程 fixture 证明客户端的参数、意图门控、退出码、JSON 与绑定处理；
公共静态校验/构建/包检查只证明资源闭包与来源字节。它们不证明引擎启动、
认证、session 恢复或真实宿主行为。[验收方案](host-evaluation.md) 定义后者。

依赖：Python 3 标准库与用户已有受控 Agent Bridge 配置。外置 Bridge 拥有
运行时/驱动/状态；插件不附带、不自动安装、不改全局配置。目标不可用时
返回原因，不自动换引擎。继续任务用准确 ID，不用 `--last`。

release acceptance 当前三个宿主均为 null（整包必需场景尚未全部验收）。已有
部分真实 Claude/Codex 场景不推广为整包支持；源码或包变化后重新绑定证据。
候选草案可准备，
stable 仍受干净 Git、规范标签与全部宿主字节绑定验收门禁约束。包清单、
Agent 输出及“approved”状态均不构成 Git、安装或发布授权。

Bridge 提供的 API 已实现，不代表每个原生安装都可用。当前 ZCode 0.16.9
的 standalone CLI 与桌面账户入口不同，不能把桌面 start-plan 凭据转成
API-key 或要求换模型来冒充兼容。新建/续接保持实际 preflight 与运行证据
判定。Codex 默认 app-server 是 Bridge 内部原生会话通路，不表示本插件
提供原生 MCP profile，也不扩大 Codex read-only 的支持声明。
