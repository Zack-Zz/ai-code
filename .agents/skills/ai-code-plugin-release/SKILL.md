---
name: ai-code-plugin-release
description: "在 ai-code 仓库新建或维护插件、准备版本与双语说明、验证发行包，并按授权使用 GitHub 一键构建发布。Use for ai-code plugin authoring, maintenance, local version preparation, and authorized GitHub build/publication."
---

# ai-code 插件开发与发布

本技能是仓库内部维护入口，不是发行插件。不要注册到 `catalog.json`、加入插件
资源白名单或复制到公开包；不要为使用它修改全局配置或宿主缓存。

## 先确定本次工作范围

- 分清咨询、方案、实现、本地版本准备、Git 交付、实际发布和安装。分析结论不会
  自动授权业务修改；版本准备、commit/push、公开 Release 和安装各有授权边界。
- 先读[根规则](../../../AGENTS.md)，检查分支、工作区和已有本次授权；修改插件前
  读取 `plugins/<id>/AGENTS.md`，保留无关改动。
- 用户已明确授权的本次操作，完成 Review 和必要验证后继续，不重复索要确认。
  没有相应授权时完成可审阅的本地成果，再交付结果与剩余步骤。

按当前任务读取对应指南，不复制或一次性加载全部文档：

| 任务 | 现有入口 |
|---|---|
| 新建插件 | [插件接入](../../../docs/plugin-authoring.md) |
| 维护现有插件、开发试用 | [开发指南](../../../CONTRIBUTING.md) |
| 本地版本准备、发行检查、Actions | [发布指南](../../../docs/publishing.md) |
| 已提供验收材料、声明宿主通过或导出摘要 | [证据契约](../../../docs/release-evidence.md) |

命令从仓库根运行；接口有疑问时查看 `python3 tooling/plugin_tool.py <子命令> --help`
和当前源码。带日期的历史记录不能代替本轮验证。

## 制作或维护插件

- `plugins/<id>/product.json` 是身份、版本、宿主和资源白名单的唯一来源；根
  `package.json`、适配模板、catalog 和已发布记录都不是第二个开发版本源。
- 新插件按实际能力声明 `hosts`，为每个声明宿主提供原生适配；资源显式登记，
  Markdown 引用闭包完整，同一共同资源在各宿主包中保持相同哈希。
- 新插件在 catalog 只登记相对目录路径。至少提供一个可发现的正式测试入口：
  `tests/skills/run-skills.js` 或 `tests/run_python_tests.py`，确认统一门禁实际执行它。
- 要接入一键发行，还须配置 `release.json`、双语发行输入，并更新
  [release.yml](../../../.github/workflows/release.yml) 的 `plugin` choices；同步
  [工作流契约测试](../../../tests/test_marketplace_workflow.py) 中当前的选项约束。
- 外部 README、安装、使用和配置说明中英双语，默认英文、顶部双向切换，链接保持
  所选语言。行为变更先有效 RED、再最小 GREEN；环境错误不算 RED。
- Codex 公开发行元数据的 `defaultPrompt` 每项最多 128 字符；以 `release check`
  验证公开输入，不能仅因 `validate` 通过就认定发行合格。

## 本地准备版本

用户只需给目标插件、版本和改动说明。AI 依据实际改动起草双语正文，写入安全的
UTF-8 临时文件，包含 `### English` 与 `### 中文`，不要写版本标题；macOS 使用
物理路径 `/private/tmp`，避免符号链接路径。

```sh
python3 tooling/plugin_tool.py release prepare-version --plugin ID --version VERSION --notes-file /private/tmp/plugin-notes.md
python3 tooling/plugin_tool.py release prepare-version --plugin ID --version VERSION --notes-file /private/tmp/plugin-notes.md --apply
```

先执行默认预览，检查计划和旧证据失效项，再在用户授权的本地准备范围内应用。
按工具计划重置过期引用、移除被识别的生成摘要；保留私有材料与历史发行记录。
不要手写 `accepted` 或 `acceptance-proof.json`、伪造实测或忽略坏证据。

版本仅允许 `X.Y.Z` / `X.Y.Z-preview.N`，数字无前导零；发行种类及 `ID/vVERSION`
标签由版本派生，不能自由组合发行种类或 prerelease 标志。draft 是本地检查模式，
不等于 GitHub Draft，也不改变版本的发行种类。

## 验证与 Git 交付

标准检查如下；`ID`、`HOST` 和包路径取自实际插件与构建索引，输出目录须不存在或为空。
修改公共工具时使用 `--all` 构建；定向修改可按插件构建并检查其所有声明宿主包。

```sh
python3 tooling/plugin_tool.py validate --all
PYTHONDONTWRITEBYTECODE=1 npm test
npm run lint
python3 .github/scripts/check_no_dist.py --root .
python3 tooling/plugin_tool.py build --plugin ID --host all --output /private/tmp/ai-code-packages
python3 tooling/plugin_tool.py package check --path /private/tmp/ai-code-packages/HOST/ID --host HOST --root .
python3 tooling/plugin_tool.py release check --plugin ID --mode draft
```

本地未提交工作区用 draft 检查合法；不要为提交前检查运行 CI 的 `--from-main`
冻结辅助程序，它可能创建本地标签或切换源码。需要完整发行 bundle 时按发布指南
运行 `release prepare` / `release verify`，从可信源码独立复验。不得手改 `published/`
或公开市场清单，`dist/` 不得进入提交。stable 技术就绪要求干净冻结 Git、规范标签
和独立包复验；本地 draft 通过不能替代这一结论。

Review 实际 diff、测试结果和剩余风险，只暂存本次授权文件；有本次 commit/push
授权则继续交付，否则保留未提交结果。Git 交付完成不代表公开发布或安装已获授权。

## GitHub 一键构建与发布

唯一手动入口是 main 上的 **Build & publish plugins / 构建与发布插件**，输入只有
`plugin` 与 `operation=build|publish`；版本与说明读取已提交源码。

- `build` 完整构建并复验、保存 Actions artifacts，不写远端标签、Release 或市场。
- `publish` 需要用户本次公开发行授权；创建或复用不可变标签，回读完整附件后公开
  Release。正式版自动同步市场，preview 只公开 Prerelease。没有发行授权时交付
  上述手动入口和具体字段，不代为启动 publish。
- 保留 `plugin-release` / `plugin-marketplace` 环境保护；配置审核人时等待环境批准，
  不绕过批准、不 force push、不移动标签或覆盖同版本资产。
- 已授权启动的远端运行必须取终态并核对回执；分别报告 Release、正式市场同步和
  宿主实测。市场失败可在公开字节未变且完整核验后重跑同版本 publish；坏回执、
  不完整资产或发布状态不明时先核查，不能 clobber。同版本公开字节变化须新版本。
- `null` / pending 宿主不阻断技术发布，仍标记 `unverified`；提供的证据必须严格验真。
  可选 acceptance-export 要全部声明宿主真实验收。构建、发布成功不证明宿主加载、
  自动调用或行为通过；安装另需用户授权和原生流程。

调用示例：`$ai-code-plugin-release 帮我准备 CodeVow 1.0.3，改动说明是……`
交付具体文件、版本、关键 diff、实际验证与未验证项；远端操作另附运行与 Release 链接。
