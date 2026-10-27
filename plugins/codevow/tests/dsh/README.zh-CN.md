# 隔离 DeepSeek Harness API 检查

[English](README.md) | 简体中文

此独立入口构建两个 DSH 包，通过官方 Loader 与 PresetRegistry 加载未经改写的 overlays，
验证 Reviewer 全部插件激活、预设挂载，以及真实工具列表仅包含 `read`、`grep` 和 `glob`。
它还使用已发布的真实 Cordis、AgentRegistry、Tools 与 Skill API，Agent 与工具定义为
测试对象，无模型和用户 profile。覆盖原生工具拒绝、scope 切换、技能提供方与生命周期，
不代表完整 Web profile、真实文件工具或模型场景验收。缺依赖直接失败；普通 `npm test`
运行本地契约组，不以跳过此入口冒充集成通过。

[英文页](README.md)提供精确版本的完整重放命令。依赖只安装到 `/private/tmp` 的一次性工程，
使用独立 npm cache、`--ignore-scripts`、`--save-exact`，保留生成的 lockfile。测试从仓库根调用：

```sh
DSH_NATIVE_NODE_MODULES=/private/tmp/codevow-native-api/node_modules \
  node plugins/codevow/tests/dsh/native-api.mjs
```

本轮使用 Node.js `v24.4.1`；构建需要 Python 3.11+。脚本校验两份 bundle 的真实 peer 版本、实际 patch 的 RC2 配置，
加载各插件自身技能，核算官方渲染后的 workflow 长度，并通过真实 Tools 管线验证拒绝。
不会读写宿主 profile、全局配置或凭据。
