# ai-code

[English](README.md) | 简体中文

一个承载多个 **AI 相关插件** 的仓库。每个插件独立维护源码、身份、版本、
资源、测试与支持声明；公共工具负责目录注册、源校验、可复现构建和本地市场
生成，插件行为留在各自目录内。

首个插件是 **CodeVow · AI 编码工作流**（`ai-code-workflow`），用于 AI 编码助手的
工程协作。其他插件形态在有具体需求时扩展；仓库不要求所有插件具备工作流
技能、策略或任务记录。

## 插件目录

| 插件 | 用途 | 版本与支持状态 |
|---|---|---|
| [CodeVow](plugins/ai-code-workflow/README.zh-CN.md) | 计划、TDD、排查、审查、验证与交付证据 | `1.0.2` 自建市场试用候选；[真实宿主验收仍未完成](plugins/ai-code-workflow/docs/support-matrix.md) |
| [Agent Delegation](plugins/ai-agent-delegation/README.md) | 通过外置Agent Bridge明确交接给其他工具或同工具独立会话 | `0.1.0`源码候选；[整包宿主验收未完成](plugins/ai-agent-delegation/docs/support-matrix.md)，未加入已发布preview市场 |

`catalog.json` 只登记插件目录；各目录的 `product.json` 是插件 ID、版本和
资源白名单的唯一来源。根目录的私有 Node 包用于仓库维护，其版本不作为
任何插件的发行版本。

项目边界见[总体架构](docs/architecture.md)与[文档导航](docs/README.md)。
派发插件保持普通开发及原生子代理行为；运行时、CLI/MCP/API由ai-mcp承载。

## 从 preview 市场安装 CodeVow

[CodeVow 1.0.2](https://github.com/Zack-Zz/ai-code/releases/tag/ai-code-workflow%2Fv1.0.2)
和 [preview 市场](https://github.com/Zack-Zz/ai-code/tree/codex/marketplace-preview)
均已发布。这是 prerelease，宿主会自动获取插件，用户无需手工下载 ZIP、
拉取源码或自行构建。安装验证与完整工作流验收分别记录，当前结果见
[原生安装记录](docs/reviews/2026-10-09-preview-marketplace-native-installation.md)。

### Codex

首次注册市场，再安装 CodeVow：

```sh
codex plugin marketplace add Zack-Zz/ai-code --ref codex/marketplace-preview
codex plugin add ai-code-workflow@ai-code-preview
```

已在 Codex CLI `0.154.0` 验证：安装并启用了 `1.0.2`，40 个安装文件与
公开插件包逐字节一致。使用前新建宿主会话；工作流行为仍待验收。
市场刷新尝试发生超时，更新能力尚未验证。

### Claude Code

Claude Code `2.1.292` 或更高版本，一条命令注册并安装：

```sh
claude plugin install ai-code-workflow --marketplace \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/codex/marketplace-preview/.claude-plugin/marketplace.json
```

`2.1.224`–`2.1.291` 使用注册、安装两步：

```sh
claude plugin marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/codex/marketplace-preview/.claude-plugin/marketplace.json
claude plugin install ai-code-workflow@ai-code-preview
```

archive 来源要求 `2.1.224` 或更高版本。参见官方
[archive 来源说明](https://code.claude.com/docs/en/plugins/marketplace-reference#archive-plugin-source)
与[安装命令](https://code.claude.com/docs/en/discover-plugins#add-and-install-from-your-shell)。
已用官方 `2.1.295` CLI 验证一键安装：安装并启用了 `1.0.2`，35 个文件
与公开 Claude 包逐字节一致，同版本市场刷新也成功。工作流行为和跨版本
升级仍待验收；本机默认 CLI 启动器仍为 `2.1.177`，更新尚未通过验证。
上述命令须使用已更新的兼容 CLI；启动器结果在原生安装记录中单独跟踪。

### ZCode

直接注册 ZCode 的 JSON 清单 URL。ZCode `3.14.5` 注册这个多宿主 Git
仓库时会优先选 Claude 市场清单。

已在 macOS 验证应用内置的原生 CLI（`0.16.9`）：

```sh
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins marketplace add \
  https://raw.githubusercontent.com/Zack-Zz/ai-code/refs/heads/codex/marketplace-preview/marketplace.json
node /Applications/ZCode.app/Contents/Resources/glm/zcode.cjs plugins install ai-code-workflow@ai-code-preview
```

已安装并启用 `1.0.2`，发现了 6 个技能，35 个安装文件与 ZCode Release
包逐字节一致，其他已安装插件保持原状态。使用前新建 ZCode 会话；
工作流行为仍待验收。

## 下载 Release 作为备用方式

打开 [CodeVow 1.0.2](https://github.com/Zack-Zz/ai-code/releases/tag/ai-code-workflow%2Fv1.0.2)，
在 **Assets** 中下载对应宿主的 ZIP；这些包无需下载源码或自行构建。
此版本为 prerelease，真实宿主验收仍未完成。

| 宿主 | 下载资产 |
|---|---|
| Claude Code | `ai-code-workflow-1.0.2-claude.zip` |
| Codex | `ai-code-workflow-1.0.2-codex.zip` |
| ZCode | `ai-code-workflow-1.0.2-zcode.zip` |

同时下载 `SHA256SUMS`，解压前将 ZIP 的 SHA256 与其中
`downloads/<资产文件名>` 条目比较。例如在 macOS/Linux 上执行：

```sh
shasum -a 256 ~/Downloads/ai-code-workflow-1.0.2-zcode.zip
```

将 ZIP 解压到长期保留的目录，并保留隐藏文件。每个下载包包含
`ai-code-workflow/` 和名为 `ai-code-local` 的本地市场，然后按宿主安装：

- **Claude Code：** 执行 `claude plugin marketplace add /path/to/extracted/claude`，
  再执行 `claude plugin install ai-code-workflow@ai-code-local`。
- **Codex：** 执行 `codex plugin marketplace add /path/to/extracted/codex`，
  重启支持插件的桌面客户端，在插件目录中选择 `ai-code-local` 并安装 CodeVow。
  CLI 不同时先查看 `codex plugin marketplace --help`。
- **ZCode：** 在插件设置中添加解压后的 `marketplace.json` 或其所在目录为市场，
  再安装并启用 CodeVow。

上述路径应替换为对应宿主 ZIP 的实际解压目录。安装后新建宿主会话，确认插件
加载。以 `-plugin.zip` 结尾的资产只包含插件，供发行市场使用，不含上述本地
市场；GitHub 自动提供的 **Source code** 下载是开发源码。

校验与更新的详细说明见[安装指南（英文）](plugins/ai-code-workflow/docs/installation.md)。
Release 与 preview 市场分支分别发布，此版本两者均已完成；完整宿主验收
和跨版本升级仍待验证。

## 开发者快速开始

在仓库根目录执行，需要 Python 3.11+ 与 Node 22+：

```sh
python3 tooling/plugin_tool.py list
python3 tooling/plugin_tool.py validate --all
npm test
python3 tooling/plugin_tool.py build --all --host all --output dist-check
python3 tooling/plugin_tool.py package check \
  --path dist-check/codex/ai-code-workflow --host codex --root .
```

输出目录必须不存在或为空。只处理一个插件时，将 `--all` 替换为
`--plugin ai-code-workflow`。`--host` 支持 `claude`、`codex`、`zcode` 与 `all`，
各插件只为自己声明的宿主生成产物。

发行目录包含名为 `ai-code-local` 的聚合本地市场、独立插件包和独立 ZIP。
每个 ZIP 只包含该插件与对应的单插件市场；解压到稳定目录后，通过宿主原生
插件机制注册并安装。操作见插件的
[安装文档](plugins/ai-code-workflow/docs/installation.md)。
三端发布预检、制品准备/复验、仓库市场和手动 GitHub 草稿流程见
[发布指南](docs/publishing.md)。稳定制品要求真实宿主验收证据。

schema 2 发行套件新增 `installers/ID-VERSION-HOST-plugin.zip`，仅含一个
插件根及完整原生包（含 artifact.json），不带市场；下载包和投稿包保持
各自用途。每个插件独立 Release，经审阅的 distribution 计划为 Claude/ZCode
选择固定资产，为 Codex 固定版本目录提交；人工 Publish 后再单独部署市场。
试用/正式市场目标分支为 `codex/marketplace-preview` 与 `codex/marketplace`。
远端发布与市场部署分别记录。三端安装及制品字节均已验证，
跨版本升级和工作流行为仍待验收；迁移期间保留现有 dist 和 ai-code-local 入口。

源校验、包完整性和测试通过不代表原生加载成功或模型遵循技能。真实宿主验收
及其证据由各插件分别维护。

## 仓库结构

| 路径 | 用途 |
|---|---|
| `catalog.json` | 显式注册的插件目录列表 |
| `distribution.json` | 渠道分支、市场名及限定运输类型，不复制插件版本 |
| `plugins/<id>/` | 插件自包含的源码、清单、资源、适配、测试与文档 |
| `tooling/plugin_tool.py` | 公共校验、构建、包检查、市场同步、release 和本地 distribution plan/check 入口 |
| `tooling/` | 通用源校验、构建与市场生成工具 |
| `tests/` | 公共工具测试与统一门禁 |
| `docs/plugin-authoring.md` | 新插件接入及宿主声明指南 |
| `docs/publishing.md` | 三端发布资料、制品、验收和渠道操作 |
| `.github/workflows/release.yml` | 手动准备制品，可选创建 GitHub 草稿 |
| `docs/design/2026-10-07-multi-plugin-design.md` | 多插件边界、数据契约与迁移计划 |
| `dist/` | 从已注册源码生成、可重建的发行目录 |

## 开发与验证

- 修改前读取根 `AGENTS.md` 和目标插件的局部维护规则。
- 行为变更使用有意义的 RED、GREEN 测试；`npm test` 覆盖公共工具与全部
  已注册插件的测试组。
- 安装本地维护依赖后执行 `npm run lint`。
- 插件 ID、版本独立维护；所有入包资源都必须登记；不同插件的源码和哈希
  边界保持清晰。
- 接入步骤见[作者指南](docs/plugin-authoring.md)。新的运行集成需要独立设计
  和宿主验证。

CodeVow 的策略解析、任务记录与带回执暂存工具仍位于源码中的
`plugins/ai-code-workflow/scripts/workflow_tool.py`，随包入口为
`tools/workflow_tool.py`；这些能力属于该插件。

## 许可证与来源

MIT——见 [LICENSE](LICENSE) 与 [NOTICE](NOTICE)。仓库早期历史派生自
Affaan Mustafa 的 ai-code。CodeVow 的迁移来源与保留的
backend-engineering-lite 许可证见该插件的
[README](plugins/ai-code-workflow/README.zh-CN.md) 和
[迁移文档](plugins/ai-code-workflow/docs/migration.md)。
