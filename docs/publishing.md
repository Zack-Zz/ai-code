# ai-code 三宿主发布（更新于 2026-10-09）

当前实施采用[main 统一分发设计](design/2026-10-09-main-marketplace-distribution-design.md)：
源码与公开市场都在 `main`，同一插件 ID 只有一个当前正式入口。新预览版只
公开为 GitHub Prerelease；正式版通过验收并成功同步后才更新入口。本文描述
本地已实施的工具与工作流职责，真实 Actions、环境审核、main 安装及升级
仍需实际验证，不表示远端已经部署。

CodeVow `1.0.2` 是已经公开的历史 Prerelease，旧
`codex/marketplace-preview` 分支保留为固定试用来源，不继续发布新版本。
三端原生安装与包字节的历史结果见
[2026-10-09 原生安装记录](reviews/2026-10-09-preview-marketplace-native-installation.md)。
该结果不证明完整工作流、跨版本升级或新 main 链路。CodeVow 与 Agent
Delegation 的开发注册都不等于正式发行；迁移后的根正式市场为空，首个正式
版本通过验收并成功同步后才有可安装入口。用户示例见[根 README](../README.zh-CN.md)。

## 1. 身份、版本与发行状态

各插件 `product.json` 是开发身份、版本、宿主、公开 publisher 与资源白名单
的唯一来源，`release.json` 只配置说明和声明宿主的验收路径。根 Node 包为
private 维护工具，不提供插件版本，也不执行 npm publish。

新的公开版本仅接受 `X.Y.Z` 与 `X.Y.Z-preview.N`，数字禁止前导零，不接受
其他后缀或 build metadata。统一比较为 `preview.2 < preview.10 < 同核心正式版`；
各插件独立推进版本、规范标签 `ID/vVERSION` 和 Release。同版本不同字节
拒绝，新事件或旧版本不得倒退市场当前指针。

| 新公开版本 | 本地验收模式 | GitHub Prerelease | 是否同步默认市场 |
|---|---|---|---|
| `X.Y.Z-preview.N` | draft | true | 否 |
| `X.Y.Z` | stable | false | 全部 stable 门禁通过后同步 |

GitHub Draft 只表示尚未公开，和本地 `mode=draft/stable` 的验收门禁分开。
新发行种类从版本派生，不能任意组合版本、mode 和 prerelease 标志。历史
`1.0.2` 的 numeric Prerelease 保留原标签、状态与附件，不改名、覆盖或改标志
转为正式版；历史套件继续按原始 schema/mode 复验。下一版本另行确定，
文中的版本语法不是创建标签或发布授权。

公开资源必须与冻结标签提交的 Git blob 字节一致；被忽略但登记入包的资源
也不得漏在标签之外。原始私有验收材料只验证哈希，不要求公开或提交。
publisher 仅是公开署名，不代表官方认证。commit、push、tag 与发布须分别
取得本次明确授权，记录或 approved 标记不代替用户决定。

## 2. 本地预检、准备与复验

在仓库根运行，输出必须不存在或为空；建议放在仓库外。Python 工具要求
3.11+ 和 POSIX 受控目录读写，其他系统未验收。原生技能文本不依赖 Python。

```sh
npm ci --no-audit --no-fund
python3 tooling/plugin_tool.py validate --all
npm test
npm run lint
python3 .github/scripts/check_no_dist.py --root .
python3 tooling/plugin_tool.py release check --plugin ai-code-workflow --mode draft
python3 tooling/plugin_tool.py release prepare --plugin ai-code-workflow --mode draft --output /tmp/codevow-release
python3 tooling/plugin_tool.py release verify --plugin ai-code-workflow --path /tmp/codevow-release
```

以上是本地候选检查，不是新公开发行。`draft` 可报告未提交和未验收事实，
仍拒绝无效资料、错误路径、错误字节绑定及不完整制品。`stable` 必须有干净
Git、规范现有标签和全部声明宿主的真实字节绑定验收。新的 numeric 正式
发行不会因本地 draft 通过而获得公开资格。查看 `publication_ready`、
`pending_acceptance` 和 `limitations`；`ok: true` 仅表示所选模式通过。

`verify` 从可信源码独立重建闭包和 ZIP 内容；制品自报哈希不能替代它。
旧套件的 `bundle_provenance` / `bundle_readiness` 保留历史，`current_source`
报告当前状态，两者来源一致且都满足资格时才可报告 publication_ready。

准备下一版本时可为 `check/prepare/verify` 指定
`--previous /可信旧发行套件/release.json`。工具核验旧包实际文件及归档，拒绝
降级和同版本内容变化。调用者须选取可信历史，本地完整性不证明曾经公开；
该参数不会自动查询 GitHub。所有本地步骤均不安装、上传或修改 Git。

## 3. 制品、临时开发市场和 dist

| 产物 | 用途 |
|---|---|
| `packages/` | 三宿主目录、单插件 ZIP、本地市场与索引 |
| `installers/ID-VERSION-HOST-plugin.zip` | 单插件完整 native package 与 artifact.json，供原生市场安装 |
| `downloads/ID-VERSION-HOST.zip` | 解压后注册本地市场的试用包 |
| `submissions/openai/ID-VERSION.zip` | 唯一插件根的 OpenAI skills-only 投稿包 |
| `submissions/claude/`、`submissions/zcode/` | 渠道源码套件与登记项，供检查及人工提交 |
| `release.json`、`SHA256SUMS`、`release-notes.md` | 来源、资格、文件闭包和哈希 |

新准备的 release manifest 为 schema 2。installer 不带本地市场，与已检查的
native package 字节一致；下载 ZIP 带本地市场；投稿套件不含原始会话或
artifact.json。schema 1 历史包继续复验，不补造新 installer。

开发市场只能生成到显式空输出目录，不覆盖公开根清单：

```sh
python3 tooling/plugin_tool.py marketplace sync --output /tmp/ai-code-development
```

该目录包含注册源码的三端构建市场。显式试用时注册
`/tmp/ai-code-development/<host>`，本地市场名为 `ai-code-local`；开发注册和
构建成功不表示已上线。各插件 ZIP 只含自身包和匹配的单插件市场。

`dist/` 是被忽略、可重建的本地/CI 临时输出，不能进入新 Git 提交或远端
分支。CI 用 `git ls-files -z -- dist` 拒绝跟踪文件，包括 `git add -f` 强制
加入的文件；不要求提交 dist 或将其与新构建比较。GitHub Actions 在临时
目录构建并逐包核验，Actions artifact 用于任务留档，公开 ZIP 保存为
Release 附件。既有历史标签与 Git 内容不因新排除规则而改写。

## 4. main 公开快照与迁移

根 `distribution.json` 维护 main、一个市场身份、latest-stable 策略和固定
宿主运输方式，不复制插件版本。内部市场名沿用已上线的 `ai-code-preview`，
不新建 stable 别名或第二个预览插件 ID，也不按整个仓库的最新 Release 时间
替代逐插件版本比较。

| 路径 | 权威或来源 |
|---|---|
| `.agents/plugins/marketplace.json` | Codex 的 main 公开入口 |
| `.claude-plugin/marketplace.json` | Claude Code 的 main 公开入口 |
| `marketplace.json` | ZCode 的 main 公开入口 |
| `published/index.json` | 各插件已成功同步的正式版本与记录引用 |
| `published/releases/ID/VERSION.json` | 不可变的正式发行、冻结源码 S 与制品记录 |
| `published/marketplaces.lock.json` | 受管公开清单的所有权和哈希回执 |
| `published/codex/ID/VERSION/` | Codex 原生安装内容，清单固定实际分发提交 D |

`product.json` 是开发版本，`published/index.json` 是上线版本，两者允许不同。
Claude 使用固定 Release archive URL/SHA256，ZCode 使用固定 ZIP URL/SHA256
和 path；Codex 使用 main 仓库中的受管版本目录并固定 D。`published/codex/`
仅保留宿主协议必需的正式安装内容，不是将完整 dist 改名入 Git。

公开快照检查只读核对冻结 S、安装内容、D 的固定引用及所有权回执：

```sh
python3 tooling/plugin_tool.py marketplace check --root .
```

旧根开发市场仅在三个清单与既有 ownership 回执完全一致时，才能迁移为空
正式快照；未知内容、人工编辑、链接或特殊文件均拒绝覆盖。审阅并授权
迁移后使用：

```sh
python3 tooling/plugin_tool.py marketplace initialize --migrate --root .
```

迁移使用被忽略的 `.marketplace-initialize.json` 保存最初已验证的字节基准；
写入中断后重复同一命令可继续。恢复时各文件只能是原值或目标值，遇到人工
修改即拒绝覆盖。完成前重验全部目标，成功后移除恢复记录；未完成的记录
会使 `marketplace check` 失败。每个文件原子替换，不能保证多文件与外部编辑
同时操作时具有整体事务性。

迁移不删除历史 Release、旧 preview 分支或用户安装。空市场不回退到预览
版；首个正式版本尚未上线前，main 用户安装命令暂不可用。旧试用步骤与
宿主版本边界见[历史安装记录](reviews/2026-10-09-preview-marketplace-native-installation.md)。

## 5. 真实宿主验收

CodeVow 当前 `release.json.acceptance` 的三个槽仍为 `null`；本轮不修改这些
实际状态。真实加载、运行场景并核对结果后，记录宿主、模型、插件与包哈希、
命令、会话和结论，再填写本插件的相对证据路径。格式见
[发行证据契约](release-evidence.md)。静态、脚本与包哈希通过不能证明宿主行为。

工具核对绑定，不证明外部会话真实性，也不将 accepted 解释为发布授权。
原始材料只在本地验证，公开包只含状态与绑定哈希；发布者仍须审阅资源
白名单，避免主动把敏感材料登记为公开资源。新主线至少需要连续两个正式
版本的安装、升级及最终加载验证；Codex 历史刷新超时须重新排查。

## 6. Prepare、Publish 与显式 Sync

[Release plugin](../.github/workflows/release.yml) 从 main 的
`workflow_dispatch` 接收 `plugin`、已有 `source_tag` 和
`operation=prepare|publish`。可信管理工具取自 main，冻结源码独立 checkout；
先验证 `ID/vVERSION`、标签提交和 `origin/main` 可达性，再运行只读权限的
测试/lint与准备。不会将 GitHub token 交给冻结源码的工具。

`prepare` 推导 preview→draft、stable→stable，校验、准备并独立复验 bundle，
保存 30 天 Actions artifact。`publish` 依赖准备结果，在 `plugin-release`
环境审核后由独立写入 job 创建 Draft、上传全部附件，逐件回读字节并再次
核对源码标签，然后由独立公开 helper 发布为对应的 Prerelease 或正式
Release；公开后继续回读。已有同版本 Release 拒绝覆盖，不创建标签。

正式标签须包含经维护者审核的 `release/acceptance-proof.json`。先在能读取
私有材料的本地运行 `release acceptance-export --plugin ID`，再将仅含哈希
的摘要与源码提交并冻结标签；Actions 显式复验其 Git 绑定、公开输入和所有
宿主包哈希。原始日志与验收 JSON 正文不进入 Git、Actions artifact 或
Release。默认本地验收仍要求实际私有材料，详见[证据契约](release-evidence.md)。

Draft helper 的职责仍只创建草稿，公开步骤使用 `publish_release.py`。
schema 2 附件含三端 installer、三端下载 ZIP、SHA256SUMS、完整套件 ZIP
及其 SHA256、发行记录和说明。Actions artifact 保留 native 隐藏目录，
公开前使用可信 main 工具验证下载后的完整闭包。

公开动作后无法确认状态时返回 uncertain，不能报告已完成发布，也不自动
重试、覆盖或删除；人工检查远端再决定后续。标签保护、环境审核和运行时
contents:write 权限仍须实测，不能从 YAML 声明推导已经生效。

正式公开成功后，发布流程显式调用本地可复用
[Sync plugin marketplace](../.github/workflows/marketplace.yml)。preview 到
Release 为止，不调用同步。不能依赖 GITHUB_TOKEN 公开 Release 或 push main
自动触发后续工作流。调用同步的 job 授予 contents:write 权限上限，内部
plan job 明确降为只读，deploy job 才在 `plugin-marketplace` 审核后写入。
两个受保护环境的入口都是 main，不用标签事件替代 main 部署入口。

## 7. 审阅 main 计划与部署

Sync 支持 `workflow_call` 及 main 的手工 `workflow_dispatch`。手工入口默认
`action=plan`；`deploy` 必须提供已审阅的计划哈希和 main 基础 SHA，不接受
absent。可复用调用先产出可下载计划与 summary，审核后使用该次计划的
hash/base 部署。全仓市场更新串行，不能让多插件同时覆盖基准。

以下示例假定 `PLUGIN_ID` 和 `SOURCE_TAG` 已设为选定插件与既有、已公开的
正式标签。`/path/to/frozen-source` 为标签 S 的 checkout，
`/path/to/trusted-main` 为可信 main 管理代码：

```sh
python3 /path/to/trusted-main/.github/scripts/deploy_marketplace.py \
  --root /path/to/frozen-source --control-root /path/to/trusted-main \
  --plugin "$PLUGIN_ID" --source-tag "$SOURCE_TAG" --channel stable \
  --action plan --output /tmp/remote-market-plan.json
```

审阅 Release ID、源码 S、附件哈希、完整路径变更、main 基准和计划哈希；
明确授权后使用同一输入和实际已审阅值：

```sh
python3 /path/to/trusted-main/.github/scripts/deploy_marketplace.py \
  --root /path/to/frozen-source --control-root /path/to/trusted-main \
  --plugin "$PLUGIN_ID" --source-tag "$SOURCE_TAG" --channel stable \
  --action deploy --expected-plan-hash "$REVIEWED_HASH" \
  --expected-market-commit "$REVIEWED_MAIN_SHA" --output /tmp/deploy-result.json
```

部署器用可信工具重验公开 Release、规范标签、全部附件和 stable 门禁，
不会执行附件自带验证器。只更新选定插件、根公开清单及 published 受管内容，
范围外文件与 Git 对象保持不变；未知内容或人工修改拒绝覆盖。计划标记
不构成写入授权，输入、字节或基础 SHA 改变即停止。

声明 Codex 的插件先形成安装目录提交 D，旧入口保持不变；再形成发行
记录、当前指针、市场和回执提交 C，Codex 清单固定实际 D。未声明 Codex
时跳过目录提交。使用普通 fast-forward，不 force push，不删旧发行。
同版本同字节幂等成功；同版本不同字节或降级事件拒绝。

Release 已公开但市场失败时，状态是“已发布，市场待更新”，旧入口保持
可用。只写完 D 则保留未引用目录，重新计划前先回读相同字节；只有 C 完成
并回读一致才报告市场部署完成。远端 main 更新和新宿主链路仍需实际运行
验证，本轮本地测试不代替这些证据。

## 8. 官方收录参考（当前不使用）

**Claude Code**：先通过自身市场分发，原生清单为
`.claude-plugin/plugin.json`。实际投稿前执行当地版本的
`claude plugin validate --strict <插件目录>` 并做真实安装会话。当前官方文档
将 Anthropic directory 的申请指向开发者门户；该目录与
`claude-plugins-official` 官方市场是不同入口，后者收录需咨询官方渠道。
本机制先生成 Claude Code 源码套件，不承诺其 Code-only Agent 在其他应用
可用，也不代填旧表单或默认通过 PR 投稿。
[Claude 发布文档](https://code.claude.com/docs/en/plugins/publish)

**Codex / OpenAI**：CodeVow 无 MCP，使用 portable 根 plugin.json 的 skills-only
路径；开发者认证、后台上传独立投稿 ZIP、审核、获批后人工发布。原生字段
和图标检查在本地执行，但目录资格及最终分类由后台决定。目前工具实现
SVG/PNG 图标及已核对的 Developer Tools、Productivity 分类子集；不代表平台
所有合法格式或分类。未来加入 MCP、hooks、apps 时需独立设计和渠道验证，
当前发布 profile 会拒绝这些组件。
[OpenAI 提交要求](https://developers.openai.com/plugins/deploy/submission)、
[唯一根 ZIP 规则](https://developers.openai.com/plugins/deploy/submission-errors)

**ZCode**：Fork 官方插件仓库，将 `submissions/zcode/` 中所需源码和登记项
人工合并到 Fork；保留官方其他插件条目，不整份覆盖其市场。运行官方
`scripts/validate.py`、`scripts/build_dist.py`，完成真实 ZCode 验证，再由用户
授权提交 PR；维护者负责审核和发布。HTTPS ZIP 市场的 URL/SHA256/path 协议
是另一种分发方式，当前源码套件不自动提供线上 URL。
[ZCode 贡献要求](https://github.com/zai-org/zcode-plugins/blob/main/CONTRIBUTING_CN.md)、
[分发协议](https://github.com/zai-org/zcode-plugins/blob/main/docs/distribution_CN.md)

根 Node 包为 private 维护工具，不执行 npm publish。正式发布前核对
[支持矩阵](../plugins/ai-code-workflow/docs/support-matrix.md) 和各渠道当时要求。
