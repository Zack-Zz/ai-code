# ai-code 维护者发布指南

[English](publishing.md) | 简体中文

先在本地准备版本和说明，审阅并提交源码，再使用 GitHub Actions 的
[Build & publish plugins / 构建与发布插件](../.github/workflows/release.yml)。
这是构建制品、公开 Release 和更新正式市场的唯一手动入口。用户安装见
[安装指南](installation.zh-CN.md)，源码开发见
[开发指南](../CONTRIBUTING.zh-CN.md)。

## 让 AI 准备版本

例如：“帮我准备 CodeVow 1.0.3：增加本地版本准备命令，简化发布流程。”
给出目标版本和改动说明即可，由 AI 起草中英说明并准备源码 diff 供审阅。

可使用本仓库的项目技能
[$ai-code-plugin-release](../.agents/skills/ai-code-plugin-release/SKILL.md)，例如：
“用 $ai-code-plugin-release 准备 CodeVow 1.0.3，检查并审阅改动后按本次授权交付 Git。”

本地 helper 读取非空 UTF-8 Markdown 正文，包含 `### English` 和 `### 中文`
两个段落，不含版本标题。例如由 AI 写入 `/private/tmp/codevow-1.0.3-notes.md`：

```markdown
### English

- Add local version preparation and simplify publishing.

### 中文

- 增加本地版本准备命令，简化发布流程。
```

从仓库根目录先预览，再应用本地修改：

```sh
python3 tooling/plugin_tool.py release prepare-version --plugin ai-code-workflow --version 1.0.3 --notes-file /private/tmp/codevow-1.0.3-notes.md
python3 tooling/plugin_tool.py release prepare-version --plugin ai-code-workflow --version 1.0.3 --notes-file /private/tmp/codevow-1.0.3-notes.md --apply
```

默认命令不写文件。`--apply` 只更新目标插件的 `product.json` 版本和
`release.json` 声明的说明文件，插入该版本章节并保留历史。已有完全相同章节
幂等；同版本说明冲突或降版拒绝执行。若新字节使旧宿主证据失效，计划明确
列出要重置的验收槽，以及要移除的有效生成摘要
`release/acceptance-proof.json`；私有材料和已发布记录保留。每项变更提供
old/new 字节和哈希，宿主验收仍报告 `unverified`。输入路径须安全且无符号
链接；macOS 临时文件可用 `/private/tmp` 等物理路径。

helper 不自动 commit、push、tag、构建、发布或安装。审阅源码 diff 与验证报告
后，明确授权本次 commit 和 push，再运行 Actions。根 private `package.json`
与适配器模板不作为插件版本来源。

## 版本与本地检查

`product.json` 是插件身份、版本、宿主、publisher 和资源白名单的唯一来源。
`release.json` 声明说明、双语 readme 和可选宿主证据路径，不复制版本。
版本只接受 `X.Y.Z` 或 `X.Y.Z-preview.N`，数字无前导零，不接受其他后缀或
build metadata；preview 序号按数字比较。标签 `ID/vVERSION` 和发行种类自动
派生。

| 版本 | GitHub Release | 市场 |
|---|---|---|
| `X.Y.Z-preview.N` | 公开 Prerelease | 不更新 |
| `X.Y.Z` | 公开正式 Release | 公开成功后自动同步 |

准备 Node.js 22+、Python 3.11+ 和支持 POSIX 文件操作的环境。本地检查与制品
准备也可独立于 Actions 执行：

```sh
npm ci --no-audit --no-fund
python3 tooling/plugin_tool.py validate --all
PYTHONDONTWRITEBYTECODE=1 npm test
npm run lint
python3 .github/scripts/check_no_dist.py --root .
python3 tooling/plugin_tool.py release check --plugin ai-code-workflow --mode draft
python3 tooling/plugin_tool.py release prepare --plugin ai-code-workflow --mode draft --output /private/tmp/codevow-release
python3 tooling/plugin_tool.py release verify --plugin ai-code-workflow --path /private/tmp/codevow-release
```

输出目录必须不存在或为空。`verify` 从可信源码独立重建资源与 ZIP 闭包。
`--previous /path/to/verified-bundle/release.json` 可对照经过完整校验的参考
套件检查版本推进。本地准备不执行发布或安装。

正式版的技术就绪要求干净且冻结的 Git 源码、规范标签、有效公开输入和独立
验证的制品。宿主验收通过 `pending_acceptance`、`accepted_hosts` 和
`limitations` 独立报告，pending 不阻断技术发布。已提供的证据与摘要仍严格
核验字节。格式见[发行证据契约](release-evidence.zh-CN.md)。

## 运行唯一 Actions 入口

在 GitHub Actions 选择 **Build & publish plugins / 构建与发布插件**，
从 **main** 运行，只需选择两个输入：

| 输入 | 选项 |
|---|---|
| `plugin` | `ai-code-workflow`、`ai-agent-delegation`、`ai-code-stack-standards` |
| `operation` | `build`、`publish` |

版本和说明读取已提交的插件源码，无需填写源码标签、计划哈希或证据路径。

- `build` 执行检查，构建完整 release bundle、原生安装 ZIP、下载包和投稿
  套件，独立复验并保存 Actions artifacts，不远端写入 tag、Release 或市场。
- `publish` 执行相同检查与构建，创建或复用规范标签，核验冻结源码，上传
  完整附件并逐件回读字节，公开对应种类的 Release。正式版随后自动调用内部
  可复用市场工作流；预览版到公开 Release 为止。

发布使用 `plugin-release` 环境，市场部署使用 `plugin-marketplace` 环境。
环境若配置 required reviewers，运行会暂停等待其批准；统一入口不绕过环境
审批。内部市场流程生成计划，将计划哈希和 main 基础提交带入部署，维护者
无需手填。

## 制品、市场记录与重试

schema 2 release bundle 包含 `packages/`、
`installers/ID-VERSION-HOST-plugin.zip`、`downloads/ID-VERSION-HOST.zip`、
`submissions/`、`release.json`、`SHA256SUMS` 与 `release-notes.md`。
公开 Release 附件包括完整 `ID-VERSION-release-bundle.zip` 及其校验文件、
各宿主下载包和原生安装 ZIP，以及发行记录。投稿套件不代表官方目录收录。

需要原生单插件包时，选择 `installers/ID-VERSION-HOST-plugin.zip`，其中是
插件目录，不额外附带本地市场清单。`downloads/ID-VERSION-HOST.zip` 是包含
本地市场与 `artifact.json` 的开发下载包。两类输出均保留，公开市场分发使用
单插件 installer。

`distribution.json` 固定 main、市场名 `ai-code` 和 latest-stable 策略；
每个插件只有一个当前正式入口。Claude Code 和 ZCode 使用固定 Release
附件；Codex 的 `published/codex/ID/VERSION/` 安装内容绑定实际分发提交。
`published/index.json`、`published/releases/ID/VERSION.json` 和
`published/marketplaces.lock.json` 保存公开记录及所有权哈希。
`product.json` 的开发版本允许与已发布版本不同。

公开清单由工具生成，不手工编辑。只读检查：

```sh
python3 tooling/plugin_tool.py marketplace check --root .
```

独立开发市场使用 `marketplace sync --output /private/tmp/ai-code-development`，
输出目录须不存在或为空，市场名为 `ai-code-local`。`dist/` 保持忽略、不提交；
公开 ZIP 保存为 Release 附件。

同版本的标签、Release 附件和已发布记录不可变。公开字节改变必须升级版本，
不能只保留原 `product.json` 版本。重跑只有在完整核验通过后才复用相同标签
和 Release。若 Release 已公开而市场更新失败，分别报告两者状态，并以相同
未变版本重跑 `publish` 继续同步；当前可用市场入口保留到验证成功的更新。
若发布结果不确定或附件不完整，先检查远端状态再重试，不能覆盖附件、移动
标签或 force push。只有 Release 与正式版市场记录均回读一致才报告完成；
宿主安装与运行验收仍独立。
