# 隔离 DeepSeek Harness API 检查

[English](README.md) | 简体中文

此独立入口构建两个 DSH 包，通过官方 Loader 与 PresetRegistry 加载未经改写的 overlays，
验证 Reviewer 全部插件激活、委派工具 `workflow_reviewer` 实际注册、预设挂载，
以及真实工具列表仅包含 `read`、`grep` 和 `glob`。
它还使用已发布的真实 Cordis、AgentRegistry、Tools 与 Skill API，Agent 与工具定义为
测试对象，无模型和用户 profile。覆盖原生工具拒绝、scope 切换、技能提供方与生命周期，
不代表完整 Web profile、真实文件工具或模型场景验收。缺依赖直接失败；普通 `npm test`
运行本地契约组，不以跳过此入口冒充集成通过。

此入口调用 `native-preset.mjs`，强制委派先加载、preset 后启用，验证等待中的委派
能够激活；还覆盖 preset 禁用后重新启用，以及委派排在首位的并行冷加载。
每次成功加载都必须实际注册 `workflow_reviewer` 工具，仅发现 preset 已登记不算通过。
适配器继承官方 AgentPreset 生命周期，将注册就绪发布为官方子代理工具的
`codevowReviewerPresetRegistered` 依赖；卸载时先撤销委派，再释放 preset 注册。

synthetic `spawn` provider 仅用于加载测试：提供注册官方委派工具所需的能力声明，
若调用其 `start` 方法则直接抛错。测试不执行模型，也不证明一次委派已经完成。
权限检查另用 fixture 工具验证真实 Tools 调用管线，挂载后的 preset 只暴露
`read`、`grep` 和 `glob`；真实文件访问和工作区隔离需另有宿主证据。

独立的 [2026-10-28 桌面探针](../../docs/verification/2026-10-28-dsh-reviewer-startup.md)
已验证发布前的 1.0.8 候选版在 DSH Desktop `0.2.1-rc.3` 原生安装并正常重启后的行为。
standard 父 Agent 仅调用一次 `workflow_reviewer`，实际派生 `codevow-reviewer` 子 Agent；
子 Agent 工具仅有 `glob`、`grep`、`read`，成功读取测试文件并完成 Review，父 Agent 收到结果。
测试文件哈希前后不变。此结果仅覆盖该只读委派及重启场景；活跃 Reviewer 中途禁用、
实际越权写调用探针、长会话和四端完整验收仍未验证。正式验收槽保持 null，CodeVow 1.0.8
已公开发布 Release 并进入正式市场。

[英文页](README.md)提供精确版本的完整重放命令。依赖只安装到 `/private/tmp` 的一次性工程，
使用独立 npm cache、`--ignore-scripts`、`--save-exact`，保留生成的 lockfile。测试从仓库根调用：

```sh
DSH_NATIVE_NODE_MODULES=/private/tmp/codevow-native-api/node_modules \
  node plugins/codevow/tests/dsh/native-api.mjs
```

本轮使用 Node.js `v24.4.1`；构建需要 Python 3.11+。脚本通过 DSH 官方兼容性判定器
验证两份 bundle 的最低运行版本和 peer 范围：拒绝 RC1 及更早版本，接受 RC2、RC3、
正式版与后续预发布版本。精确安装的 RC2 包保留为可复现的 API 组合基线；范围匹配
不代表 RC3 或更高版本的完整运行验收通过。CodeVow 另声明
`@deepseek-ai/cordis` `~4.0.5`，其 DSH peers 仍为 `>=0.2.1-rc.2`。
脚本还校验实际 patch 的 RC2 配置，
加载各插件自身技能，核算官方渲染后的 workflow 长度，并通过真实 Tools 管线验证拒绝。
不会读写宿主 profile、全局配置或凭据。
