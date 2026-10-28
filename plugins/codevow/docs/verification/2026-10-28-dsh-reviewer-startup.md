# CodeVow 1.0.8 候选：DSH Reviewer 并行启动修复与有界验证

日期：2026-10-28（Asia/Shanghai）。本文是本地修复及验证记录，不是公开发布或四端完整验收声明。

## 问题与修复

DSH Desktop `0.2.1-rc.3` 中，CodeVow 1.0.7 的技能与 Reviewer 预设组件运行，
委派组件却失败。真实 Fiber 错误为 `agent-preset/not-found`：
`Unknown agent preset: codevow-reviewer`。错误记录中的可用预设只有
`standard`、`ptc`、`minimal`、`cordis`；稍后 Reviewer 预设已经注册，失败的委派仍未恢复。

原生 Loader 并行初始化同组条目，YAML 行顺序不保证注册先后。委派工具在加载时
一次性读取配置的 preset；仅注入 `agentPresets` 服务不能保证特定 preset 已登记。

修复增加 DSH 专用 `reviewer-preset.js`，继承官方 AgentPreset 的配置、子配置解析标记
和注册生命周期。注册完成后发布 `codevowReviewerPresetRegistered`，官方委派工具将其
作为必需依赖。单一原生 effect 管理资源，卸载时先撤销信号并等待依赖方退出，再注销
preset。信号表示已注册，完整组合的诊断及活跃 generation lease 仍由宿主管理。
未使用固定延时、轮询或备用 preset。

## 源码与安装包绑定

- 本地候选：CodeVow `1.0.8`；正式 Release 与正式市场仍为 `1.0.7`。
- 基础 Git 提交：`1d0ae0c46ac5bf5df0cb82d4c6ba66dcb99e4327`；修复保留为未提交改动。
- 候选资源 `source_tree_hash`：`7bcb407292994a1bb0e7aa17362e6a2dcf49f909400067ac9169acb811f09d55`。
- DSH TGZ SHA-256：`a56bf6b0590637f6ae2d5bf0ae240e25b8a97ce044449bdcef7480445ffad728`。
- 四端包通过可信源码独立检查；DSH TGZ 的 41 个文件与已检查目录逐字节一致，
  未包含 tests、evals、设计文档、node_modules 或缓存目录。
- DSH 最低版本及 DSH peers 保持 `>=0.2.1-rc.2`；原生 Cordis peer 为 `~4.0.5`。

## 自动检查

有效 RED：先修改回归测试，让委派组件在 preset 尚未登记时加载。
`DSH_NATIVE_NODE_MODULES=/private/tmp/codevow-native-api/node_modules node plugins/codevow/tests/dsh/native-api.mjs`
退出 1，失败原因正是 `Unknown agent preset: codevow-reviewer`，而非环境或缺包错误。

修复后的检查：

| 检查 | 结果与边界 |
|---|---|
| `npm test` | 6 组全部通过，包含新增注册就绪与有序清理单元测试 |
| `npm run lint` | 通过 |
| `validate --all` | 通过 |
| `release check --plugin codevow --mode draft` | 通过；不代表正式发布就绪 |
| 四端 `package check` | 全部通过 |
| 隔离原生 API 入口 | 21 项通过，使用精确 RC2 包与 Cordis 4.0.5 |

原生回归覆盖 preset 延迟注册、注册失败、注册途中卸载、禁用后重新启用、委派排在首位的
并行冷加载，并断言 `workflow_reviewer` 实际注册。原生预设的真实工具列表仍只有
`read`、`grep`、`glob`；独立工具管线用 fixture 验证禁止写入、shell、再委派及越权工具。
加载回归中的 synthetic spawn provider 不执行模型，与下方真实桌面验证分开报告。

## 真实 DSH Desktop 验证

使用桌面应用自带的原生 CLI 安装已检查的本地包，保留原 profile 清单备份：

```sh
"/Applications/DeepSeek Harness.app/Contents/Resources/runtime/cli/bin/dsh" plugin \
  --profile desktop add --ignore-scripts \
  /private/tmp/codevow-reviewer-startup-zxo1z7kk/packages/dsh/codevow-1.0.8.tgz
```

正常退出并重启桌面应用后，插件页显示 `v1.0.8`、共 3 组件、3 运行中。
已安装的 41 个文件与上述 TGZ 对应目录逐字节一致。

在原生界面创建临时工作区和 standard 预设会话，要求主智能体只委派一次 Reviewer，
自身不打开测试文件。测试文件包含事先生成、未写入提示词的随机校验值和一个明确的
折扣计算错误。真实会话记录确认：

1. 父会话仅调用一次 `workflow_reviewer`，工具返回成功并给出子会话 ID。
2. 子会话 header 的 `origin` 为 `subagent`，`agentPreset` 为 `codevow-reviewer`，
   `parentSession` 正确指向该父会话；执行 provider 为 `spawn`。
3. 子会话的请求头实际只包含 `glob`、`grep`、`read` 三个工具；实际调用 `read` 和 `glob`，均成功。
4. 子任务准确返回随机校验值，指出 `discount.py` 第 4 行把折扣相加的错误。
5. 子任务正常完成，父会话接收到完成通知并总结结果；测试文件 SHA-256 前后相同。
6. 此后读取宿主真实 Loader 状态，CodeVow 三个组件均为 ACTIVE，没有保留失败错误。

原始测试会话、截图、包检查、RED/GREEN 日志仅保存在本机
`/private/tmp/codevow-reviewer-startup-zxo1z7kk/`，不进入发行包。
两份原始压缩会话捕获的 SHA-256 为：

- 子会话：`2604d936db1c28baae342a347c47ad07a4cf5910fe5ac0ee51791e4a4c13497d`。
- 父会话：`b77395fd86a02d17ecf59a221f99117934922df4a2fdaf3a2c2afef836f053d3`。

原生安装提示了 peer 警告；单独运行 `dsh plugin --profile desktop peers check` 返回 1，
列出 profile 本地未安装的宿主依赖。已核对这些 CodeVow peers 在 Desktop 的 ASAR 中
提供相应版本，包括 Cordis 4.0.5 与 DSH RC3；上述真实加载、委派及工具调用成功。
不将独立 pnpm peer 检查记为通过，也未为消除该提示另外安装宿主内置依赖。

## 验证范围

主代理负责 TDD、实现、集成和真实桌面验证；`architecture_advisor` 提供有界的原生
生命周期建议，`code_implementer` 维护四份双语测试/支持说明，`code_reviewer` 独立核读
实现、上游 API、失败证据和回归用例，未发现确认缺陷。独立审查为源码检查，没有代替
主代理执行测试或实际宿主验证。

已验证本机 RC3 桌面端的冷重启加载及一次真实只读 Reviewer 委派。
尚未验证桌面端活跃 Reviewer 中途禁用/升级、真实禁止写调用探针、长会话、完整工作区隔离，
以及 Claude Code、Codex、ZCode 的本轮真实运行。隔离生命周期回归不能替代这些宿主场景。

`release.json` 的正式 acceptance 槽仍为 null；本次有界探针不构成四端完整验收。
本轮没有提交、推送、标签、公开 Release 或正式市场更新。
