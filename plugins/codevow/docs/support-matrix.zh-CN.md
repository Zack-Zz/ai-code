[English](support-matrix.md) | 简体中文

# 当前支持与验证边界

当前正式版为 `codevow` 1.0.8，声明 Claude Code、Codex、ZCode、DeepSeek Harness 四个制品目标。
公开 DSH 包和索引的 `engines.dsh` 与 DSH peers 均声明最低 `>=0.2.1-rc.2`，RC3 及更高版本
可通过此版本门槛；API 基线仍为已发布 RC2 的 Web profile。范围匹配不代表未来 API
兼容已经验证。
必须提供原生 preset、Agent、工具、提示词与 spawn 服务；缺依赖由原生 Loader 报告无法激活。
Reviewer 的 read/grep/glob 白名单与文件系统隔离分别记录，读取权限根复用宿主配置。四端 acceptance 保持 null。

仅本地结构、单元测试和包检查不证明原生加载、自动调用、权限执行、安装或生命周期验收。
[英文页中的历史记录](support-matrix.md)保留原有日期、命令和结论，不构成本轮通过。

## Reviewer 启动修复（CodeVow 1.0.8，2026-10-28）

1.0.8 正式版修复 DSH Desktop RC3 的 Reviewer 启动顺序问题。1.0.7 并行加载时，
委派可能先于 preset 注册而启动，报 `Unknown agent preset codevow-reviewer`，
随后 preset 虽已出现，失败的委派仍不能恢复。适配器继承官方 AgentPreset
生命周期，让官方子代理工具等待 `codevowReviewerPresetRegistered` 依赖；卸载时先
撤销委派，再释放 preset 注册。CodeVow 新增 Cordis peer `~4.0.5`，DSH 最低版本及
DSH peers 保持 `>=0.2.1-rc.2`。

[隔离的已发布 API 检查](../tests/dsh/README.zh-CN.md)覆盖委派先加载、preset 后启用、
禁用后重新启用、并行冷加载、`workflow_reviewer` 实际注册，以及挂载后真实的
read/grep/glob 工具列表。测试使用真实 RC2 Loader 与原生服务，但 synthetic spawn
provider 不执行模型，不证明模型委派已完成、真实文件系统隔离或完整宿主验收。

独立的 [2026-10-28 桌面探针](verification/2026-10-28-dsh-reviewer-startup.md)已验证发布前的 1.0.8 候选版
在 DSH Desktop `0.2.1-rc.3` 原生安装、正常重启后 3 个组件全部运行，安装目录的 41 个文件
与已校验的包一致。新建临时工作区会话中，standard 父 Agent 仅调用一次
`workflow_reviewer`，实际派生 `codevow-reviewer` 子 Agent，父子会话绑定正确。
子 Agent 工具仅有 `glob`、`grep`、`read`，实际 read/glob 调用成功，指出测试文件中的错误，
完成 Review 后父 Agent 收到结果；测试文件哈希前后不变。

此结果仅覆盖该只读委派及重启场景。活跃 Reviewer 中途禁用、实际越权写调用探针与
长会话仍未验证；`acceptance.dsh` 保持 null，未宣称完整 DSH 或四端 acceptance 全部通过。
CodeVow 1.0.8 已公开发布 Release 并进入正式市场。
