# ai-code 维护者发布指南

[English](publishing.md) | 简体中文

本指南说明当前发行工具和工作流。用户安装见[安装指南](installation.zh-CN.md)，
源码开发见[开发指南](../CONTRIBUTING.zh-CN.md)。发布前检查与验收记录在维护
文档中管理，用户 README 只说明当前功能、安装和使用。

## 发行输入与版本

插件 `product.json` 是身份、版本、宿主、署名和公开资源白名单的唯一来源。
`release.json` 声明说明文件与各宿主验收路径，不复制版本。根 Node 包为 private
维护工具，不执行 npm publish。

版本仅使用 `X.Y.Z` 或 `X.Y.Z-preview.N`，数字无前导零，不接受其他后缀或
build metadata。工具按数字比较版本，拒绝降级和同版本不同字节。
规范源码标签为 `ID/vVERSION`。

| 版本 | 本地模式 | GitHub Prerelease | main 市场 |
|---|---|---|---|
| `X.Y.Z-preview.N` | draft | true | 不更新 |
| `X.Y.Z` | stable | false | 正式成功后同步 |

GitHub Draft 表示尚未公开，与本地 `mode=draft/stable` 分开。发行种类由版本
派生。Git 提交、标签、公开发行和市场部署分别需要本次明确授权。

## 本地检查与制品准备

准备 Node.js 22+、Python 3.11+ 和支持 POSIX 文件操作的环境。命令从仓库根
执行，输出目录必须不存在或为空，建议放在仓库外。

```sh
npm ci --no-audit --no-fund
python3 tooling/plugin_tool.py validate --all
PYTHONDONTWRITEBYTECODE=1 npm test
npm run lint
python3 .github/scripts/check_no_dist.py --root .
python3 tooling/plugin_tool.py release check --plugin ai-code-workflow --mode draft
python3 tooling/plugin_tool.py release prepare --plugin ai-code-workflow --mode draft --output /tmp/codevow-release
python3 tooling/plugin_tool.py release verify --plugin ai-code-workflow --path /tmp/codevow-release
```

`draft` 用于本地准备；`stable` 要求干净 Git、规范标签与全部声明宿主的字节
绑定验收。查看报告的 `publication_ready`、`pending_acceptance` 和
`limitations`。本地命令不安装插件、不上传制品，也不修改 Git。

`verify` 从可信源码独立重建资源和 ZIP 闭包。若要核对版本推进，可使用
`--previous /path/to/verified-bundle/release.json`；参考套件仍须经过完整字节
校验，同版本不能改变内容。

## 制品与开发市场

当前 release manifest 使用 schema 2。不同产物的用途如下：

| 产物 | 用途 |
|---|---|
| `packages/` | 宿主安装目录、插件 ZIP、本地市场和索引 |
| `installers/ID-VERSION-HOST-plugin.zip` | 完整单插件原生包，不带市场 |
| `downloads/ID-VERSION-HOST.zip` | 带本地市场的手动下载包 |
| `submissions/openai/ID-VERSION.zip` | skills-only 投稿包 |
| `submissions/claude/`、`submissions/zcode/` | 渠道源码套件与登记项 |
| `release.json`、`SHA256SUMS`、`release-notes.md` | 发行记录、文件闭包、校验值和说明 |

开发市场只生成到显式空输出目录：

```sh
python3 tooling/plugin_tool.py marketplace sync --output /tmp/ai-code-development
```

各宿主目录的市场名为 `ai-code-local`。试用步骤见开发指南。
`dist/` 是被忽略的临时输出，不提交；公开 ZIP 保存为 Release 附件。

## main 市场记录

`distribution.json` 维护 main、市场名 `ai-code`、latest-stable 策略和
宿主运输方式。同一插件 ID 只有一个当前正式入口。

| 路径 | 内容 |
|---|---|
| `.agents/plugins/marketplace.json` | Codex 入口 |
| `.claude-plugin/marketplace.json` | Claude Code 入口 |
| `marketplace.json` | ZCode 入口 |
| `published/index.json` | 已同步的正式版本与记录引用 |
| `published/releases/ID/VERSION.json` | 不可变正式记录与冻结源码 |
| `published/marketplaces.lock.json` | 受管清单及哈希回执 |
| `published/codex/ID/VERSION/` | Codex 原生安装内容 |

Claude Code 和 ZCode 使用固定 Release 附件；Codex 入口固定实际分发提交。
`product.json` 维护开发版本，`published/` 维护市场版本。

公开快照检查为只读操作：

```sh
python3 tooling/plugin_tool.py marketplace check --root .
```

空市场不使用预览版替代正式入口。公开清单不手工编辑，正式发行通过下面的
市场计划与部署流程更新。

## 宿主验收与公开摘要

对插件声明的每个宿主执行真实安装和任务场景，核对版本、加载内容、授权边界
和结果，再记录证据。格式见[发行证据契约](release-evidence.zh-CN.md)。

在能读取私有材料的本地完成验收后，执行：

```sh
python3 tooling/plugin_tool.py release acceptance-export --plugin ai-code-workflow
```

工具生成 `release/acceptance-proof.json`，只导出经核验的哈希声明。维护者审核
后将摘要与最终公开源码冻结在规范标签中，原始材料留在私有路径。Actions
显式使用 committed 验收，不读取或公开私有正文。摘要是事实声明，不产生
发布授权，也不代替真实宿主测试。

## Prepare、Publish 与市场同步

[Release plugin](../.github/workflows/release.yml) 从 main 的手工入口接收
`plugin`、已有 `source_tag` 和 `operation=prepare|publish`。

1. Prepare 使用 main 的可信管理工具读取冻结标签，核验标签格式与 main 可达性，执行测试、静态检查、制品准备与独立复验，保存 Actions artifact。
2. Publish 在 `plugin-release` 环境审核后创建 Draft、上传完整附件、逐件回读并核对冻结标签，再公开为对应种类的 Release。已有同版本 Release 不覆盖，流程不创建标签。
3. 正式版公开成功后显式调用 [Sync plugin marketplace](../.github/workflows/marketplace.yml)。预览版到 Release 为止。

源码标签的公开输入必须与 Git blob 字节一致；Actions artifact 保留原生隐藏
目录。公开后继续回读状态，无法确认时报告 uncertain，不自动重试或删除。

市场同步的 plan 只读；deploy 经 `plugin-marketplace` 环境审核，并要求实际
已审阅的计划哈希和 main 基础 SHA。人工执行示例：

```sh
python3 /path/to/trusted-main/.github/scripts/deploy_marketplace.py \
  --root /path/to/frozen-source --control-root /path/to/trusted-main \
  --plugin "$PLUGIN_ID" --source-tag "$SOURCE_TAG" --channel stable \
  --action plan --output /tmp/remote-market-plan.json
```

审阅 Release、源码、附件哈希、路径变更和 main 基准；授权后按同一输入部署：

```sh
python3 /path/to/trusted-main/.github/scripts/deploy_marketplace.py \
  --root /path/to/frozen-source --control-root /path/to/trusted-main \
  --plugin "$PLUGIN_ID" --source-tag "$SOURCE_TAG" --channel stable \
  --action deploy --expected-plan-hash "$REVIEWED_HASH" \
  --expected-market-commit "$REVIEWED_MAIN_SHA" --output /tmp/deploy-result.json
```

上述变量来自选定插件、已公开正式标签和实际审阅结果，不使用占位值执行。
部署器重验 Release、标签、全部附件和 stable 门禁。Codex 安装目录与市场
记录分阶段提交，只有市场记录回读一致才报告同步完成。基础提交或字节变化
时停止；使用普通 fast-forward，不 force push。

Release 已公开而市场更新失败时，分别报告两个结果，并保留当前可用市场入口。
官方目录投稿属于独立人工渠道，生成的 submission 套件不代表官方收录。
